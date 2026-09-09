<!DOCTYPE html>
<html>
<head>
    <title>Fruit Catcher Mini-Game</title>
    <style>
        #basket {
            position: absolute;
            left: 50%;
            transform: translateX(-50%);
            bottom: 10px;
            width: 80px;
            height: 80px;
            background-color: yellow;
        }
        
        .fruit {
            position: absolute;
            width: 40px;
            height: 40px;
            background-color: red;
        }
        
        #score {
            font-size: 24px;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <h1>Fruit Catcher Mini-Game</h1>
    <h2>Score: <span id="score">0</span></h2>
    <div id="basket"></div>

    <script>
        // Variables
        var score = 0;
        var basket = document.getElementById('basket');
        var scoreDisplay = document.getElementById('score');

        // Move the basket
        document.addEventListener('keydown', function(event) {
            var basketPos = basket.offsetLeft;
            var step = 20;
            
            if (event.key === 'ArrowLeft') {
                basket.style.left = basketPos - step + 'px';
            } else if (event.key === 'ArrowRight') {
                basket.style.left = basketPos + step + 'px';
            }
        });

        // Create and animate fruits
        setInterval(function() {
            var fruit = document.createElement('div');
            fruit.classList.add('fruit');
            fruit.style.left = getRandomPosition() + 'px';

            var gameArea = document.body.getBoundingClientRect().width;
            var fallSpeed = Math.floor(Math.random() * 5) + 1;

            document.body.appendChild(fruit);

            var interval = setInterval(function() {
                var fruitPos = fruit.offsetTop;
                fruit.style.top = fruitPos + fallSpeed + 'px';

                if (fruitPos > window.innerHeight) {
                    clearInterval(interval);
                    document.body.removeChild(fruit);
                }

                // Check collision with basket
                if (fruitPos > window.innerHeight - basket.offsetHeight && fruitPos + fruit.offsetHeight > window.innerHeight - basket.offsetHeight) {
                    var basketPos = basket.offsetLeft;
                    if (fruitPos > window.innerHeight - basket.offsetHeight && fruitPos + fruit.offsetHeight > window.innerHeight - basket.offsetHeight && fruitPos + fruit.offsetHeight < window.innerHeight - basket.offsetHeight + basket.offsetHeight && fruit.offsetLeft > basketPos && fruit.offsetLeft < basketPos + basket.offsetWidth) {
                        score++;
                        scoreDisplay.innerHTML = score;
                        document.body.removeChild(fruit);
                        clearInterval(interval);
                    }
                }
            }, 10);
        }, 1000);

        // Helper function to get random horizontal position
        function getRandomPosition() {
            var gameArea = document.body.getBoundingClientRect().width;
            return Math.floor(Math.random() * (gameArea - 40));
        }
    </script>
</body>
</html>
