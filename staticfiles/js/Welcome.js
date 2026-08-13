document.addEventListener('DOMContentLoaded', () => {
            const container = document.getElementById('rainContainer');
            const dropCount = 100; // Adjust for density

            for(let i = 0; i < dropCount; i++) {
                const drop = document.createElement('div');
                drop.classList.add('drop');
                
                // Randomize positions and animation details
                const leftPos = Math.random() * 100;
                const delay = Math.random() * 2;
                const duration = Math.random() * 0.8 + 0.6; // Between 0.6s and 1.4s
                const opacity = Math.random() * 0.5 + 0.2;
                const height = Math.random() * 20 + 80; // 80px to 100px long

                drop.style.left = `${leftPos}%`;
                drop.style.animationDelay = `${delay}s`;
                drop.style.animationDuration = `${duration}s`;
                drop.style.opacity = opacity;
                drop.style.height = `${height}px`;

                container.appendChild(drop);
            }
        });
