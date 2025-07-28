const hexToRGB = (hex, alpha) => {
    const r = parseInt(hex.slice(1, 3), 16),
        g = parseInt(hex.slice(3, 5), 16),
        b = parseInt(hex.slice(5, 7), 16);

    return "rgba(" + r + ", " + g + ", " + b + ", " + alpha + ")";
}
const root = document.querySelector(':root');
let hexCol = getComputedStyle(root).getPropertyValue('--color-primary').trim()
const colVal = hexToRGB(hexCol, 0.25);
root.style.setProperty('--color-primary-rgba', colVal);
hexCol = getComputedStyle(root).getPropertyValue('--color-primary')


//color settings
 
const colorLayer = document.querySelector('color')
if (colorLayer) {
    const primary = colorLayer.getAttribute("theme"), secondary = colorLayer.getAttribute('secondary'), tab = colorLayer.getAttribute('tab')
    root.style.setProperty('--color-primary', primary)
    root.style.setProperty('--color-tab', tab)
    root.style.setProperty('--color-secondary', secondary)
}