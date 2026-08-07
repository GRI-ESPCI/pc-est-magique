/**
 * Casino marquee bulbs — shared across all casino pages.
 * Computes positions along a rounded rectangle and places SVG circles.
 */
document.addEventListener('DOMContentLoaded', () => {
    function getPointAtLength(t, w, h, rx, inset) {
        const sw = Math.max(0, w - 2*inset - 2*rx);
        const sh = Math.max(0, h - 2*inset - 2*rx);
        const c = Math.PI * rx / 2;
        const p = 2*sw + 2*sh + 4*c;
        t = ((t % p) + p) % p;
        
        function getRadius(t_corner) {
            return rx;
        }

        if (t <= sw) return { x: inset + rx + t, y: inset };
        t -= sw;
        if (t <= c) {
            const angle = -Math.PI/2 + (t/c) * (Math.PI/2);
            const r = getRadius(t);
            return { x: inset + rx + sw + r * Math.cos(angle), y: inset + rx + r * Math.sin(angle) };
        }
        t -= c;
        if (t <= sh) return { x: w - inset, y: inset + rx + t };
        t -= sh;
        if (t <= c) {
            const angle = (t/c) * (Math.PI/2);
            const r = getRadius(t);
            return { x: inset + rx + sw + r * Math.cos(angle), y: inset + rx + sh + r * Math.sin(angle) };
        }
        t -= c;
        if (t <= sw) return { x: inset + rx + sw - t, y: h - inset };
        t -= sw;
        if (t <= c) {
            const angle = Math.PI/2 + (t/c) * (Math.PI/2);
            const r = getRadius(t);
            return { x: inset + rx + r * Math.cos(angle), y: inset + rx + sh + r * Math.sin(angle) };
        }
        t -= c;
        if (t <= sh) return { x: inset, y: inset + rx + sh - t };
        t -= sh;
        const angle = Math.PI + (t/c) * (Math.PI/2);
        const r = getRadius(t);
        return { x: inset + rx + r * Math.cos(angle), y: inset + rx + r * Math.sin(angle) };
    }

    function updateMarqueeBulbs() {
        document.querySelectorAll('.casino-marquee-bulbs').forEach(svg => {
            const bbox = svg.getBoundingClientRect();
            if (bbox.width === 0) return;
            
            const isMain = svg.classList.contains('main-bulbs');
            const targetGap = isMain ? 36 : 28;
            const inset = isMain ? 12 : 9;
            const rx = isMain ? 18 : 15;
            const bulbRadius = isMain ? 4 : 3;
            
            const sw = Math.max(0, bbox.width - 2*inset - 2*rx);
            const sh = Math.max(0, bbox.height - 2*inset - 2*rx);
            const perimeter = 2*sw + 2*sh + 2*Math.PI*rx;
            
            let numBulbs = Math.round(perimeter / targetGap);
            numBulbs = Math.round(numBulbs / 4) * 4;
            if (numBulbs < 4) numBulbs = 4;
            
            const actualGap = perimeter / numBulbs;
            const offset = sw / 2;
            
            let htmlOff = '';
            let htmlOnOdd = '';
            let htmlOnEven = '';
            for (let i = 0; i < numBulbs; i++) {
                const pt = getPointAtLength(offset + i * actualGap, bbox.width, bbox.height, rx, inset);
                const circle = `<circle cx="${pt.x.toFixed(2)}" cy="${pt.y.toFixed(2)}" r="${bulbRadius}"></circle>`;
                htmlOff += circle;
                if (i % 2 === 0) htmlOnEven += circle;
                else htmlOnOdd += circle;
            }
            
            let gOff = svg.querySelector('.bulbs-off-group');
            let gOnOdd = svg.querySelector('.bulbs-on-group-odd');
            let gOnEven = svg.querySelector('.bulbs-on-group-even');
            if (!gOff) {
                svg.innerHTML = '';
                gOff = document.createElementNS('http://www.w3.org/2000/svg', 'g');
                gOff.setAttribute('class', 'bulbs-off-group');
                svg.appendChild(gOff);
                
                gOnOdd = document.createElementNS('http://www.w3.org/2000/svg', 'g');
                gOnOdd.setAttribute('class', 'bulbs-on-group-odd');
                svg.appendChild(gOnOdd);

                gOnEven = document.createElementNS('http://www.w3.org/2000/svg', 'g');
                gOnEven.setAttribute('class', 'bulbs-on-group-even');
                svg.appendChild(gOnEven);
            }
            gOff.innerHTML = htmlOff;
            gOnOdd.innerHTML = htmlOnOdd;
            gOnEven.innerHTML = htmlOnEven;
        });
    }

    // ResizeObserver with debounce to prevent layout thrashing
    let resizeTimeout;
    const resizeObserver = new ResizeObserver(() => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(updateMarqueeBulbs, 100);
    });
    document.querySelectorAll('.casino-marquee-bulbs').forEach(svg => resizeObserver.observe(svg));
    setTimeout(updateMarqueeBulbs, 50);
});
