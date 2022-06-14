function change_display(id_h2) {
    let elem_h2 = document.getElementById(id_h2);
    let elem_div = document.getElementById("block_" + id_h2);
    if (elem_div.style.display == "none"){
        elem_h2.innerHTML = elem_h2.innerHTML.slice(0, -1) + "&#9650;";
        elem_div.style.display = "block";
    }
    else {
        elem_h2.innerHTML = elem_h2.innerHTML.slice(0, -1) + "&#9660;";
        elem_div.style.display = "none";
    }
}