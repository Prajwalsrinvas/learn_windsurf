import json
import os
import string
from collections import Counter

import nltk
from flask import Flask, jsonify, render_template_string, request

from color_palette import get_all_color_palettes
from wiki_cache_utils import get_cache_path, save_result_cache
from wiki_category_word_freq import (download_nltk_resources,
                                     get_all_category_members, get_page_text)

app = Flask(__name__)

# Simple HTML template with JS for word cloud and palette selection
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wikipedia Word Cloud</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        html, body { height: 100%; margin: 0; overflow: hidden; }
        #wordcloud svg { width: 100%; height: 100%; }
        .app-container { height: 100vh; display: flex; flex-direction: column; }
        .cloud-container { flex: 1; min-height: 0; position: relative; }
        /* Make the word cloud container bigger and more prominent */
        #wordcloud { min-height: 70vh; transition: all 0.3s ease; }
        #progress { z-index: 100; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .animate-spin { animation: spin 1s linear infinite; }
    </style>
</head>
<body class="bg-gray-50">
    <div class="app-container">
        <!-- Header with controls -->
        <header class="bg-white shadow-md py-4 px-6">
            <div class="max-w-7xl mx-auto">
                <div class="flex flex-col lg:flex-row items-center justify-between gap-4">
                    <h1 class="text-3xl font-bold text-blue-700">Wikipedia Word Cloud</h1>
                    
                    <form id="cat-form" class="flex flex-col md:flex-row items-center gap-3 w-full lg:w-auto">
                        <div class="flex flex-col md:flex-row gap-3 w-full">
                            <input type="text" id="category" name="category" value="Physics" required 
                                placeholder="Wikipedia Category" 
                                class="border border-gray-300 rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 w-full md:w-64"/>
                            
                            <div id="palette-select" class="w-full md:w-48"></div>
                        </div>
                        
                        <button type="submit" 
                            class="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 py-2 rounded shadow transition">Generate</button>
                    </form>
                </div>
                
                <div class="flex items-center justify-between mt-3">
                    <div id="palette-colors" class="flex gap-2"></div>
                    <div class="text-gray-600 font-medium">
                        <span id="category-title" class="font-semibold text-gray-800"></span>
                    </div>
                </div>
            </div>
        </header>
        
        <!-- Main content area with word cloud -->
        <main class="cloud-container bg-white p-4">
            <div id="wordcloud" class="w-full h-full bg-gray-50 rounded-lg border border-gray-200"></div>
            <div id="progress" class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-white p-4 rounded-lg shadow-lg hidden">
                <div class="flex flex-col items-center">
                    <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mb-3"></div>
                    <div id="progress-text" class="text-gray-700 font-medium">Fetching data...</div>
                    <div id="progress-detail" class="text-gray-500 text-sm mt-1"></div>
                </div>
            </div>
        </main>
    </div>
    <!-- d3 and d3-cloud via CDN -->
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script src="https://unpkg.com/d3-cloud/build/d3.layout.cloud.js"></script>
    <script>
    let palettes = {};
    let selectedPalette = null;
    // Fetch palettes and populate dropdown
    fetch('/palettes').then(r => r.json()).then(data => {
        palettes = data;
        let select = document.createElement('select');
        select.id = 'palette';
        select.className = 'border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 w-full';
        for (let name in palettes) {
            let opt = document.createElement('option');
            opt.value = name;
            opt.textContent = name;
            select.appendChild(opt);
        }
        select.onchange = function() {
            selectedPalette = this.value;
            showPaletteColors();
            // Do NOT auto-generate cloud on palette change
        };
        document.getElementById('palette-select').appendChild(select);
        selectedPalette = select.value;
        showPaletteColors();
    });
    function showPaletteColors() {
        let colors = palettes[selectedPalette] || [];
        let html = colors.map(c => `<span style="display:inline-block;width:32px;height:20px;background:${c};margin:2px;border-radius:4px;border:1px solid #ccc;"></span>`).join(' ');
        document.getElementById('palette-colors').innerHTML = html;
    }
    document.getElementById('cat-form').onsubmit = function(e) {
        e.preventDefault();
        loadWordCloud();
    };
    function loadWordCloud() {
        var cat = document.getElementById('category').value;
        document.getElementById('category-title').textContent = cat;
        let palette = selectedPalette || '';
        
        // Show progress indicator
        document.getElementById('progress').classList.remove('hidden');
        document.getElementById('progress-text').textContent = 'Fetching data...';
        document.getElementById('progress-detail').textContent = 'This may take a moment for new categories';
        
        let cloud = document.getElementById('wordcloud');
        cloud.innerHTML = '';
        
        fetch(`/wordcloud?category=${encodeURIComponent(cat)}&palette=${encodeURIComponent(palette)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Hide progress indicator
                document.getElementById('progress').classList.add('hidden');
                renderWordCloud(data);
            })
            .catch(error => {
                document.getElementById('progress').classList.add('hidden');
                cloud.innerHTML = `<div class="flex items-center justify-center h-full"><p class="text-red-500">Error: ${error.message}</p></div>`;
                console.error('Error:', error);
            });
    }
    function renderWordCloud(data) {
        let container = document.getElementById('wordcloud');
        container.innerHTML = '<div class="flex items-center justify-center h-full"><span class="text-gray-400">Generating word cloud...</span></div>';
        
        if (!data || Object.keys(data).length === 0) {
            container.innerHTML = '<div class="flex items-center justify-center h-full"><i>No data available.</i></div>';
            return;
        }
        
        // Get container dimensions - ensure we have enough space for a bigger word cloud
        let width = Math.max(container.clientWidth, 1000);
        let height = Math.max(container.clientHeight, 800);
        
        // Find min/max frequency
        let values = Object.values(data);
        let min = Math.min(...values), max = Math.max(...values);
        
        // Create a better scale for font sizes - more dramatic difference between small and large words
        // Using a logarithmic scale to make the size differences more pronounced
        let fontScale = v => {
            // Ensure we don't have log(0) issues
            if (min === max) return 40; // Default size if all words have same frequency
            
            // Log scale for better visual differentiation with more pronounced size differences
            const normalized = (v - min) / (max - min || 1);
            // Increase min and max font sizes for a bigger, more impressive word cloud
            return Math.max(18, Math.min(120, 18 + 102 * Math.pow(normalized, 0.7)));
        };
        
        // Get colors from the selected palette
        let colors = palettes[selectedPalette] || ["#333"];
        
        // Sort words by frequency (highest first) and limit to top 150 for a richer word cloud
        let sortedWords = Object.entries(data)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 150)
            .map(([text, freq]) => ({
                text,
                size: fontScale(freq),
                freq
            }));
        
        // Create the layout with better settings for a cloud appearance
        let layout = d3.layout.cloud()
            .size([width, height])
            .words(sortedWords)
            .padding(5)  // More padding for better readability and separation
            .rotate(() => ~~(Math.random() * 3) * 45) // 0, 45, or 90 degrees for more variety while keeping readability
            .spiral('archimedean')  // Explicitly set spiral type
            .random(() => 0.5)  // Consistent random seed
            .font('Arial')
            .fontSize(d => d.size)
            .on('end', draw);
        
        // Start the layout calculation
        try {
            layout.start();
        } catch (e) {
            console.error('Error generating word cloud:', e);
            container.innerHTML = '<div class="flex items-center justify-center h-full"><p class="text-red-500">Error generating word cloud. Try with fewer words.</p></div>';
        }
        
        // Draw function that renders the cloud once layout is calculated
        function draw(words) {
            if (!words || words.length === 0) {
                container.innerHTML = '<div class="flex items-center justify-center h-full"><p>No words to display</p></div>';
                return;
            }
            
            container.innerHTML = '';
            
            // Create SVG with responsive sizing
            let svg = d3.select(container)
                .append('svg')
                .attr('width', '100%')
                .attr('height', '100%')
                .attr('preserveAspectRatio', 'xMidYMid meet')
                .attr('viewBox', [0, 0, width, height]);
            
            // Create group for the cloud centered in the SVG
            let g = svg.append('g')
                .attr('transform', `translate(${width/2},${height/2})`);
            
            // Add text elements for each word with enhanced styling
            g.selectAll('text')
                .data(words)
                .enter().append('text')
                .style('font-size', d => `${d.size}px`)
                .style('font-family', '"Segoe UI", Arial, Helvetica, sans-serif')
                .style('font-weight', d => d.size > 50 ? 'bold' : (d.size > 30 ? '600' : '400')) // Better weight distribution
                .style('fill', (d, i) => colors[i % colors.length]) // Cycle through palette colors
                .style('cursor', 'pointer')
                .style('opacity', 0) // Start with opacity 0 for animation
                .attr('text-anchor', 'middle')
                .attr('transform', d => `translate(${d.x},${d.y})rotate(${d.rotate})`)
                .text(d => d.text)
                // Add subtle shadow to improve contrast and legibility
                .style('text-shadow', d => d.size > 40 ? '1px 1px 2px rgba(0,0,0,0.2)' : 'none')
                // Add hover effect for interactivity
                .on('mouseover', function(event, d) {
                    d3.select(this)
                      .transition()
                      .duration(200)
                      .style('font-size', `${d.size * 1.1}px`)
                      .style('fill-opacity', 0.8);
                })
                .on('mouseout', function(event, d) {
                    d3.select(this)
                      .transition()
                      .duration(200)
                      .style('font-size', `${d.size}px`)
                      .style('fill-opacity', 1);
                })
                .transition() // Add a fade-in transition
                .duration(800)
                .delay((d, i) => i * 15) // Stagger the animations
                .style('opacity', 1) // Fade in to full opacity
                .selection() // Return to the selection for chaining
                .append('title')
                .text(d => `${d.text}: ${d.freq} occurrences`);
        }
    }
    // No initial load; only generate on button click
    </script>
</body>
</html>
"""


def compute_word_frequencies(category):
    # Download NLTK resources if needed
    download_nltk_resources()
    stop_words = set(nltk.corpus.stopwords.words("english"))

    titles = get_all_category_members(category)
    if not titles:
        return {}  # Return empty dict if no pages found

    words = []
    for title in titles:
        text = get_page_text(title)
        if not text:
            continue

        tokens = nltk.word_tokenize(text)
        for w in tokens:
            w = w.lower()
            # Filter out short words, stopwords, punctuation, and non-alphabetic words
            if (
                len(w) <= 2
                or w in stop_words
                or w in string.punctuation
                or not w.isalpha()
            ):
                continue
            words.append(w)

    # Get top 300 words to ensure we have enough for a richer visualization
    freq = dict(Counter(words).most_common(300))
    return freq


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/palettes")
def palettes():
    palettes = get_all_color_palettes()
    # Return as {name: [color1, color2, ...]}
    return jsonify({k: v.colors for k, v in palettes.items()})


@app.route("/wordcloud")
def wordcloud():
    category = request.args.get("category", "Physics")
    palette_name = request.args.get("palette", "Pastel")
    force_refresh = request.args.get("refresh", "").lower() == "true"

    cache_path = get_cache_path(category)

    # Check if we should use cache
    if not force_refresh and os.path.exists(cache_path):
        try:
            with open(cache_path, "r") as f:
                cached_data = json.load(f)
                if cached_data and len(cached_data) >= 10:
                    return jsonify(cached_data)
        except (json.JSONDecodeError, IOError):
            # If cache is corrupted, continue to recompute
            pass

    # Compute frequencies
    freq = compute_word_frequencies(category)

    # If we have enough words, save to cache
    if freq and len(freq) >= 10:
        save_result_cache(category, freq)

    return jsonify(freq)


if __name__ == "__main__":
    app.run(debug=True)
