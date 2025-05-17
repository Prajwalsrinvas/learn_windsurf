// Modern Minimal Snake Game with Moving Fruit
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const gridSize = 20;
const tileCount = canvas.width / gridSize;

const fruitEmojis = ['🍎','🍌','🍒','🍇','🍉','🍓','🍑','🍍','🥝','🥭','🍊','🍋'];
let snake = [{ x: 10, y: 10 }];
let direction = { x: 1, y: 0 };
let newDirection = { x: 1, y: 0 };
let fruit = randomFruit();
let fruitEmoji = fruitEmojis[Math.floor(Math.random() * fruitEmojis.length)];
let fruitDir = randomFruitDir();
let score = 0;
let bgColor = '#1a1a2e';
let fruitMoveCounter = 0;

function randomFruit() {
  return {
    x: Math.floor(Math.random() * tileCount),
    y: Math.floor(Math.random() * tileCount),
  };
}

function randomFruitDir() {
  const dirs = [
    { x: 1, y: 0 },
    { x: -1, y: 0 },
    { x: 0, y: 1 },
    { x: 0, y: -1 },
  ];
  return dirs[Math.floor(Math.random() * dirs.length)];
}

function drawSnake() {
  ctx.fillStyle = '#a2d5c6'; // soft mint green
  for (let i = 0; i < snake.length; i++) {
    ctx.beginPath();
    ctx.arc(
      snake[i].x * gridSize + gridSize / 2,
      snake[i].y * gridSize + gridSize / 2,
      gridSize / 2.2,
      0,
      Math.PI * 2
    );
    ctx.fill();
  }
}

function drawFruit() {
  ctx.font = `${gridSize * 0.9}px serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(
    fruitEmoji,
    fruit.x * gridSize + gridSize / 2,
    fruit.y * gridSize + gridSize / 2
  );
}

function moveSnake() {
  const head = {
    x: (snake[0].x + direction.x + tileCount) % tileCount,
    y: (snake[0].y + direction.y + tileCount) % tileCount,
  };
  snake.unshift(head);
  if (head.x === fruit.x && head.y === fruit.y) {
    score++;
    document.getElementById('score').textContent = `Score: ${score}`;
    // Change background color
    bgColor = randomColor();
    document.body.style.background = bgColor;
    // Place new fruit
    fruit = randomFruit();
    fruitEmoji = fruitEmojis[Math.floor(Math.random() * fruitEmojis.length)];
    fruitDir = randomFruitDir();
  } else {
    snake.pop();
  }
}

function moveFruit() {
  // Move fruit every 7 snake ticks (slower)
  fruitMoveCounter++;
  if (fruitMoveCounter < 7) return;
  fruitMoveCounter = 0;
  fruit.x = (fruit.x + fruitDir.x + tileCount) % tileCount;
  fruit.y = (fruit.y + fruitDir.y + tileCount) % tileCount;
  // If fruit hits wall, pick new direction
  if (
    fruit.x < 0 || fruit.x >= tileCount ||
    fruit.y < 0 || fruit.y >= tileCount
  ) {
    fruitDir = randomFruitDir();
  }
}

function randomColor() {
  // Pleasant, soft pastel random (lighter, less saturated)
  const h = Math.floor(Math.random() * 360);
  const s = 55 + Math.floor(Math.random() * 15); // 55-70%
  const l = 78 + Math.floor(Math.random() * 7);  // 78-85%
  return `hsl(${h}, ${s}%, ${l}%)`;
}

function checkCollision() {
  const [head, ...body] = snake;
  for (const part of body) {
    if (head.x === part.x && head.y === part.y) return true;
  }
  return false;
}

function gameOver() {
  ctx.fillStyle = 'rgba(0,0,0,0.6)';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#fff';
  ctx.font = '2em Segoe UI, sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText('Game Over', canvas.width / 2, canvas.height / 2 - 10);
  ctx.font = '1.2em Segoe UI, sans-serif';
  ctx.fillText(`Score: ${score}`, canvas.width / 2, canvas.height / 2 + 30);
}

function gameLoop() {
  direction = newDirection;
  moveSnake();
  moveFruit();
  if (checkCollision()) {
    gameOver();
    return;
  }
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  drawFruit();
  drawSnake();
  setTimeout(gameLoop, 170); // slower snake
}

document.addEventListener('keydown', (e) => {
  const keyMap = {
    ArrowUp: { x: 0, y: -1 },
    ArrowDown: { x: 0, y: 1 },
    ArrowLeft: { x: -1, y: 0 },
    ArrowRight: { x: 1, y: 0 },
    w: { x: 0, y: -1 },
    s: { x: 0, y: 1 },
    a: { x: -1, y: 0 },
    d: { x: 1, y: 0 },
  };
  const dir = keyMap[e.key];
  if (dir) {
    // Prevent snake from reversing
    if (snake.length > 1 && dir.x === -direction.x && dir.y === -direction.y) return;
    newDirection = dir;
  }
});

gameLoop();
