// Sort function
var table = document.getElementById("sort-table");
var rows = Array.prototype.slice.call(table.children);

var svgs = [];
svgs[1] = document.getElementById("icon-template-up");
svgs[-1] = document.getElementById("icon-template-down");

var sort_col = null;
var sort_way = 0;

function _do_sort(col, way, asFloat) {
    var svg = document.getElementById("sort-svg-" + col);
    if (way) {      // 1 ou -1 : trier
        svg.innerHTML = svgs[way].innerHTML;
        if (asFloat) {
            rows = rows.sort(
                (r1, r2) => way * ((r1.dataset[col] == r2.dataset[col]) ? 0 : (
                    (Number.parseFloat(r1.dataset[col]) > Number.parseFloat(r2.dataset[col])) ? 1 : -1
                ))
            );
        } else {
            rows = rows.sort(
                (r1, r2) => way * ((r1.dataset[col] == r2.dataset[col]) ? 0 : (
                    (r1.dataset[col] > r2.dataset[col]) ? 1 : -1
                ))
            );
        }
        rows.forEach(row => table.appendChild(row));
        // appendChild va déplacer la ligne à la fin de la table (pas de duplication implicite des nodes DOM)
    } else {        // 0 : effacer l'indicateur de tri
        svg.innerHTML = "";
    }
}

function sort(col, asFloat = false) {
    if (col != sort_col) {
        // Pas de tri sur cette colonne -> efface autre tri, et croissant
        if (sort_col)  _do_sort(sort_col, 0, asFloat);
        sort_col = col;
        sort_way = 1;
        _do_sort(col, sort_way, asFloat)
    } else {
        // Tri croissant <-> décroissant
        sort_way = -sort_way;
        _do_sort(col, sort_way, asFloat)
    }
}
