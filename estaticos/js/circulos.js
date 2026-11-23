/*
 * Gráficas de círculo (dona) del panel y de los reportes (23-nov-2026).
 *
 * Cada gráfica se declara en la plantilla con un <canvas data-dona="id">
 * y sus datos en un <script type="application/json" id="id"> (json_script);
 * si el bloque trae una lista, el lienzo elige la suya con data-dona-indice:
 *   { "etiquetas": [...], "valores": [...], "colores": ["--teal", "#ff7d00", ...],
 *     "formato": "numero" | "pesos", "centro": "texto bajo el total" }
 * En el centro va el total. Al pasar el cursor se ve el valor y su
 * porcentaje; al tocar una etiqueta de la leyenda se oculta esa parte.
 * Sin la librería (sin conexión), la leyenda en HTML sigue mostrando los datos.
 */
(function () {
    "use strict";

    var COLORES_POR_DEFECTO = ["--teal", "--green", "--orange", "--red", "--teal-claro", "--brown", "--muted"];
    var pesos = new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 });
    var compacto = new Intl.NumberFormat("es-CO", { notation: "compact", maximumFractionDigits: 1 });
    var entero = new Intl.NumberFormat("es-CO");
    var graficas = [];

    function variable(nombre) {
        return getComputedStyle(document.documentElement).getPropertyValue(nombre).trim();
    }

    function resolverColor(color) {
        return color && color.indexOf("--") === 0 ? variable(color) || "#7a6a58" : color;
    }

    function formatear(valor, formato, corto) {
        if (formato === "pesos") { return corto ? "$ " + compacto.format(valor) : pesos.format(valor); }
        return entero.format(valor);
    }

    // Total en el centro de la dona, con el texto que lo explica debajo.
    var textoCentral = {
        id: "textoCentral",
        afterDraw: function (grafica) {
            var opciones = grafica.options.plugins.textoCentral;
            if (!opciones || !grafica.getDatasetMeta(0).data.length) { return; }
            var arco = grafica.getDatasetMeta(0).data[0];
            var contexto = grafica.ctx;
            var visibles = grafica.data.datasets[0].data.filter(function (_, i) { return grafica.getDataVisibility(i); });
            var total = visibles.reduce(function (suma, valor) { return suma + valor; }, 0);
            var radio = arco.innerRadius;
            contexto.save();
            contexto.textAlign = "center";
            contexto.textBaseline = "middle";
            contexto.fillStyle = variable("--text");
            contexto.font = "700 " + Math.max(14, Math.round(radio * 0.42)) + 'px "Montserrat", sans-serif';
            contexto.fillText(formatear(total, opciones.formato, true), arco.x, arco.y - radio * 0.1);
            if (opciones.texto) {
                contexto.fillStyle = variable("--muted");
                contexto.font = "600 " + Math.max(10, Math.round(radio * 0.17)) + 'px "Open Sans", sans-serif';
                contexto.fillText(opciones.texto, arco.x, arco.y + radio * 0.32);
            }
            contexto.restore();
        }
    };

    function dibujar(lienzo) {
        var fuente = document.getElementById(lienzo.getAttribute("data-dona"));
        if (!fuente || !window.Chart) { return; }
        var datos = JSON.parse(fuente.textContent);
        // Varias donas pueden compartir un mismo bloque de datos (una lista) y elegir la suya por índice.
        if (Array.isArray(datos)) { datos = datos[Number(lienzo.getAttribute("data-dona-indice")) || 0]; }
        if (!datos) { return; }
        var colores = (datos.colores && datos.colores.length ? datos.colores : COLORES_POR_DEFECTO);
        var sinMovimiento = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        var grafica = new window.Chart(lienzo, {
            type: "doughnut",
            data: {
                labels: datos.etiquetas,
                datasets: [{
                    data: datos.valores,
                    colores: colores,
                    backgroundColor: datos.valores.map(function (_, i) { return resolverColor(colores[i % colores.length]); }),
                    borderColor: variable("--card"),
                    borderWidth: 2,
                    hoverOffset: 8
                }]
            },
            plugins: [textoCentral],
            options: {
                cutout: "64%",
                maintainAspectRatio: false,
                devicePixelRatio: (window.devicePixelRatio || 1) * (lienzo.currentCSSZoom || 1),
                animation: sinMovimiento ? false : { animateRotate: true, animateScale: false, duration: 700 },
                layout: { padding: 8 },
                plugins: {
                    textoCentral: { formato: datos.formato, texto: datos.centro || "" },
                    legend: {
                        // El panel lleva su propia leyenda con las cifras al lado.
                        display: datos.leyenda !== false,
                        position: "bottom",
                        labels: { boxWidth: 10, boxHeight: 10, usePointStyle: true, pointStyle: "circle", color: variable("--dim"), padding: 12 }
                    },
                    tooltip: {
                        callbacks: {
                            label: function (ctx) {
                                var total = ctx.dataset.data.reduce(function (suma, valor) { return suma + valor; }, 0);
                                var parte = total ? Math.round((ctx.raw / total) * 1000) / 10 : 0;
                                return " " + ctx.label + ": " + formatear(ctx.raw, datos.formato) + " (" + String(parte).replace(".", ",") + " %)";
                            }
                        }
                    }
                }
            }
        });
        graficas.push(grafica);
    }

    function iniciar() {
        if (!window.Chart) { return; }
        document.querySelectorAll("canvas[data-dona]").forEach(dibujar);
    }

    // Al cambiar entre modo claro y oscuro, las donas toman los colores nuevos.
    window.addEventListener("contanika:tema", function () {
        graficas.forEach(function (grafica) {
            var serie = grafica.data.datasets[0];
            serie.borderColor = variable("--card");
            serie.backgroundColor = serie.data.map(function (_, i) { return resolverColor(serie.colores[i % serie.colores.length]); });
            grafica.options.plugins.legend.labels.color = variable("--dim");
            grafica.update("none");
        });
    });

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", iniciar);
    } else {
        iniciar();
    }
})();
