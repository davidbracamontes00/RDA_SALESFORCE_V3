let vendedores = [];


let datosCompletos = [];


let datosFiltrados = [];


let clientesCompletos = [];


let clientesFiltrados = [];



let apvsSeleccionados = [];


let archivoExcel = null;

function aplicarTema(tema){
    const temaSeguro = tema === "light" ? "light" : "dark";
    document.documentElement.dataset.theme = temaSeguro;
    const esClaro = temaSeguro === "light";
    document.getElementById("themeLabel").textContent = `Tema: ${esClaro ? "Claro" : "Oscuro"}`;
    const boton = document.getElementById("themeToggle");
    boton.textContent = esClaro ? "🌙 Cambiar a oscuro" : "☀️ Cambiar a claro";
    boton.setAttribute("aria-label", esClaro ? "Cambiar a tema oscuro" : "Cambiar a tema claro");
    try { localStorage.setItem("rda-gac-tema", temaSeguro); } catch (error) { /* La preferencia sigue aplicándose en esta sesión. */ }
}

function alternarTema(){
    aplicarTema(document.documentElement.dataset.theme === "light" ? "dark" : "light");
}

function inicializarTema(){
    let temaGuardado = "dark";
    try { temaGuardado = localStorage.getItem("rda-gac-tema") || "dark"; } catch (error) { /* Usa el tema oscuro predeterminado. */ }
    aplicarTema(temaGuardado);
}

inicializarTema();


const tableBody =
document.getElementById(
    "tableBody"
);

const tableFooter =
document.getElementById(
    "tableFooter"
);

const vendorsContainer =
document.getElementById(
    "vendorsContainer"
);

const dropdownBtn =
document.getElementById(
    "dropdownBtn"
);

const dropdownContent =
document.getElementById(
    "dropdownContent"
);


function actualizarStatusSistema(
    mensaje
){

    const status =
    document.getElementById(
        "statusText"
    );

    if(status){

        status.textContent =
        mensaje;

    }

}

function escaparHTML(valor){
    const caracteres = {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"};
    return String(valor ?? "").replace(/[&<>"']/g, caracter => caracteres[caracter]);
}


// =====================================================
// DROPDOWN
// =====================================================

dropdownBtn.addEventListener(
    "click",
    () => {

        dropdownContent
        .classList
        .toggle(
            "active"
        );

    }
);


// =====================================================
// APV SELECCIONADOS
// =====================================================

function actualizarSeleccionados(){

    const seleccionados =
    Array.from(

        document.querySelectorAll(
            ".vendor-item input:checked"
        )

    ).map(

        checkbox => checkbox.value

    );

    apvsSeleccionados =
    seleccionados;

    document
    .getElementById(
        "selectedCount"
    )
    .innerHTML =

    `${seleccionados.length} APV seleccionados`;

}


// =====================================================
// VENDEDORES
// =====================================================

function renderizarVendedores(){

    vendorsContainer.innerHTML =
    "";

    vendedores.forEach(

        nombre => {

            const div =
            document.createElement(
                "div"
            );

            div.classList.add(
                "vendor-item"
            );

            div.innerHTML = `

                <input
                type="checkbox"
                value="${escaparHTML(nombre)}">

                <label>

                    ${escaparHTML(nombre)}

                </label>

            `;

            div.querySelector("input").addEventListener(
                "change",
                actualizarSeleccionados
            );

            vendorsContainer
            .appendChild(
                div
            );

        }

    );

    actualizarSeleccionados();

}

// =====================================================
// TOTALES
// =====================================================

function actualizarTotales(
    datos
){

    if(
        !datos ||
        datos.length === 0
    ){

        tableFooter.innerHTML = "";

        return;

    }

    const columnas = [

        "PISO",
        "LEADS MARCA",
        "LEADS BDC",
        "PROSPECCION",
        "POP-UP STORE",
        "EVENTOS",
        "REACTIVACIONES",
        "FAN PAGE",
        "DEMOS",
        "SOLICITUDES",
        "CITAS ASISTIDAS"

    ];

    const totales = {};

    columnas.forEach(

        columna => {

            totales[columna] = 0;

        }

    );

    let totalAvaluos = 0;

    datos.forEach(

        fila => {

            columnas.forEach(

                columna => {

                    totales[columna] +=
                    Number(
                        fila[columna] || 0
                    );

                }

            );

            totalAvaluos +=
            Number(
                fila.avaluos || 0
            );

        }

    );

    tableFooter.innerHTML = `

        <tr class="total-row">

            <td>
                TOTAL
            </td>

            ${columnas.map(

                columna =>

                `<td>

                    ${totales[columna]}

                </td>`

            ).join("")}

            <td>

                ${totalAvaluos}

            </td>

        </tr>

    `;

}


// =====================================================
// TABLA
// =====================================================

function renderizarTabla(
    datos
){

    tableBody.innerHTML = "";

    if(
        !datos ||
        datos.length === 0
    ){

        tableBody.innerHTML = `

            <tr>

                <td
                colspan="13">

                    No hay datos disponibles

                </td>

            </tr>

        `;

        actualizarTotales([]);

        return;

    }

    datos.forEach(

        fila => {

            const tr =
            document.createElement(
                "tr"
            );

            tr.innerHTML = `

                <td class="apv-cell">

                    ${escaparHTML(fila.APV || "")}

                </td>

                <td>${fila["PISO"] || 0}</td>

                <td>${fila["LEADS MARCA"] || 0}</td>

                <td>${fila["LEADS BDC"] || 0}</td>

                <td>${fila["PROSPECCION"] || 0}</td>

                <td>${fila["POP-UP STORE"] || 0}</td>

                <td>${fila["EVENTOS"] || 0}</td>

                <td>${fila["REACTIVACIONES"] || 0}</td>

                <td>${fila["FAN PAGE"] || 0}</td>

                <td>${fila["DEMOS"] || 0}</td>

                <td>${fila["SOLICITUDES"] || 0}</td>

                <td>${fila["CITAS ASISTIDAS"] || 0}</td>

                <td>

                    <input
                    type="number"
                    min="0"
                    value="${escaparHTML(fila.avaluos || 0)}"
                    class="manual-input"

                    >

                </td>

            `;

            tableBody.appendChild(
                tr
            );

            tr.querySelector(".manual-input").addEventListener("change", event => {
                actualizarAvaluo(fila.APV, event.target.value);
            });

        }

    );

    actualizarTotales(
        datos
    );

}

// =====================================================
// AVALUOS
// =====================================================

function actualizarAvaluo(
    apv,
    valor
){

    const numero =
    Number(valor) || 0;

    datosCompletos.forEach(

        fila => {

            if(
                fila.APV === apv
            ){

                fila.avaluos =
                numero;

            }

        }

    );

    datosFiltrados.forEach(

        fila => {

            if(
                fila.APV === apv
            ){

                fila.avaluos =
                numero;

            }

        }

    );

    actualizarTotales(
        datosFiltrados
    );

}


// =====================================================
// FILTRO APV
// =====================================================

function filtrarTabla(){

    actualizarSeleccionados();

    // ==========================
    // SIN FILTROS
    // ==========================

    if(
        apvsSeleccionados.length === 0
    ){

        datosFiltrados =
        [...datosCompletos];

        clientesFiltrados =
        [...clientesCompletos];

    }

    // ==========================
    // FILTRO APV
    // ==========================

    else{

        datosFiltrados =
        datosCompletos.filter(

            fila =>

            apvsSeleccionados.includes(
                fila.APV
            )

        );

        clientesFiltrados =
        clientesCompletos.filter(

            cliente =>

            apvsSeleccionados.includes(
                cliente.asesor
            )

        );

    }

    renderizarTabla(
        datosFiltrados
    );

    actualizarStatusSistema(

        `${datosFiltrados.length} APV visibles`

    );

}


// =====================================================
// BUSCADOR APV
// =====================================================

const searchVendor =
document.getElementById(
    "searchVendor"
);

if(searchVendor){

    searchVendor.addEventListener(
        "input",
        function(){

            const texto =
            this.value
            .toLowerCase();

            const items =
            document.querySelectorAll(
                ".vendor-item"
            );

            items.forEach(

                item => {

                    const nombre =
                    item.textContent
                    .toLowerCase();

                    item.classList.toggle(
                        "is-hidden",
                        !nombre.includes(texto)
                    );

                }

            );

        }
    );

}


// =====================================================
// SELECCION RAPIDA
// =====================================================

function seleccionarTodos(){

    document
    .querySelectorAll(
        ".vendor-item input"
    )
    .forEach(

        checkbox => {

            checkbox.checked =
            true;

        }

    );

    actualizarSeleccionados();
    filtrarTabla();

}


function limpiarSeleccion(){

    document
    .querySelectorAll(
        ".vendor-item input"
    )
    .forEach(

        checkbox => {

            checkbox.checked =
            false;

        }

    );

    actualizarSeleccionados();
    filtrarTabla();

}


// =====================================================
// CARGA VENDEDORES
// =====================================================

function cargarVendedoresDesdeDatos(){

    vendedores = [

        ...new Set(

            datosCompletos.map(

                fila => fila.APV

            )

        )

    ]

    .filter(Boolean)

    .sort();

    renderizarVendedores();

}


// =====================================================
// RESET
// =====================================================

function limpiarTabla(){

    tableBody.innerHTML = "";

    tableFooter.innerHTML = "";

    vendedores = [];

    datosCompletos = [];

    datosFiltrados = [];

    apvsSeleccionados = [];

    vendorsContainer.innerHTML = "";

    actualizarStatusSistema(
        "Sistema reiniciado"
    );

}

// =====================================================
// PROCESAMIENTO
// =====================================================

async function procesarInformacion(){

    // =====================================
    // ARCHIVOS
    // =====================================

    const prospectos =
    document.getElementById(
        "prospectosFile"
    ).files[0];

    const oportunidades =
    document.getElementById(
        "oportunidadesFile"
    ).files[0];

    const eventos =
    document.getElementById(
        "eventosFile"
    ).files[0];

    // =====================================
    // VALIDACION
    // =====================================

    const faltantes = [];

    if(!prospectos){
        faltantes.push(
            "Prospectos"
        );
    }

    if(!oportunidades){
        faltantes.push(
            "Oportunidades"
        );
    }

    if(!eventos){
        faltantes.push(
            "Eventos"
        );
    }

    if(
        faltantes.length > 0
    ){

        const mensaje =

        "Faltan archivos:\n\n" +

        faltantes.join(
            "\n"
        );

        actualizarStatusSistema(
            mensaje
        );

        alert(
            mensaje
        );

        return;

    }

    // =====================================
    // ESTADO
    // =====================================

    actualizarStatusSistema(
        "Procesando información..."
    );

    const processButton = document.getElementById("processButton");
    processButton.disabled = true;
    processButton.dataset.procesando = "true";
    processButton.textContent = "PROCESANDO…";

    document
    .getElementById(
        "processStatus"
    )
    .textContent =
    "Procesando...";

    // =====================================
    // FORM DATA
    // =====================================

    const formData =
    new FormData();

    formData.append(
        "prospectos",
        prospectos
    );

    formData.append(
        "oportunidades",
        oportunidades
    );

    formData.append(
        "eventos",
        eventos
    );

    try{

        // =====================================
        // API
        // =====================================

        const response =
        await fetch(

            "/procesar",

            {
                method:"POST",
                body:formData
            }

        );

        if(
            !response.ok
        ){

            const errorPayload = await response.json().catch(() => ({}));
            throw new Error(
                errorPayload.detail || errorPayload.mensaje || `Error HTTP ${response.status}`
            );

        }

        const resultado =
        await response.json();

        // =====================================
        // VALIDACION RESPUESTA
        // =====================================

        if(
            resultado.status !==
            "success"
        ){

            throw new Error(

                resultado.mensaje ||

                "Error en procesamiento"

            );

        }

        // =====================================
        // ARCHIVO EXCEL
        // =====================================

        archivoExcel =
        resultado.archivo_excel ||
        null;

        // =====================================
        // RESUMEN
        // =====================================

        datosCompletos = (

            resultado.datos || []

        ).map(

            fila => ({

                ...fila,

                avaluos:0

            })

        );

        datosFiltrados =
        [...datosCompletos];

        // =====================================
        // CLIENTES
        // =====================================

        clientesCompletos =
        resultado.clientes || [];

        clientesFiltrados =
        [...clientesCompletos];

        // =====================================
        // APV
        // =====================================

        cargarVendedoresDesdeDatos();

        document.getElementById("filterButton").disabled = false;
        document.getElementById("downloadButton").disabled = false;

        // =====================================
        // TABLA
        // =====================================

        renderizarTabla(
            datosFiltrados
        );

        // =====================================
        // STATUS
        // =====================================

        actualizarStatusSistema(

            `Reporte generado correctamente · ${datosCompletos.length} APV`

        );

        document
        .getElementById(
            "processStatus"
        )
        .textContent =
        `Reporte generado · ${clientesCompletos.length.toLocaleString("es-MX")} clientes`;

        console.log(
            "Reporte cargado"
        );

        console.log(
            "Resumen:",
            datosCompletos.length
        );

        console.log(
            "Clientes:",
            clientesCompletos.length
        );

    }

    catch(error){

        console.error(
            error
        );

        actualizarStatusSistema(

            "Error en procesamiento"

        );

        document
        .getElementById(
            "processStatus"
        )
        .textContent =
        "Error";

        alert(

            error.message ||

            "Error desconocido"

        );

    }

    finally{
        delete processButton.dataset.procesando;
        actualizarEstadoCarga();
        processButton.textContent = "GENERAR REPORTE";
    }

}


// =====================================================
// ARCHIVOS
// =====================================================

function actualizarNombreArchivo(
    inputId,
    statusId
){

    const input =
    document.getElementById(
        inputId
    );

    const status =
    document.getElementById(
        statusId
    );

    if(
        !input ||
        !status
    ){
        return;
    }

    input.addEventListener(
        "change",
        function(){

            if(
                this.files.length > 0
            ){

                status.textContent =
                "✓ " + this.files[0].name + " · " +
                (this.files[0].size / (1024 * 1024)).toFixed(1) + " MB";

            }

            else{

                status.textContent =
                "Sin archivo";

            }

            actualizarEstadoCarga();

        }
    );

}


actualizarNombreArchivo(
    "prospectosFile",
    "prospectosStatus"
);

function archivosCompletosSeleccionados(){
    return ["prospectosFile", "oportunidadesFile", "eventosFile"]
        .every(id => document.getElementById(id).files.length > 0);
}

function actualizarEstadoCarga(){
    const completos = archivosCompletosSeleccionados();
    const button = document.getElementById("processButton");
    if(button && !button.dataset.procesando){
        button.disabled = !completos;
    }
    const status = document.getElementById("processStatus");
    if(status && !completos){
        const faltantes = [
            ["prospectosFile", "Prospectos"],
            ["oportunidadesFile", "Oportunidades"],
            ["eventosFile", "Eventos"]
        ].filter(([id]) => !document.getElementById(id).files.length).map(([, nombre]) => nombre);
        status.textContent = `Falta cargar: ${faltantes.join(", ")}`;
    } else if(status && status.textContent.startsWith("Falta cargar:")){
        status.textContent = "Archivos listos para procesar";
    }
}

actualizarEstadoCarga();

actualizarNombreArchivo(
    "oportunidadesFile",
    "oportunidadesStatus"
);

actualizarNombreArchivo(
    "eventosFile",
    "eventosStatus"
);



// =====================================================
// DESCARGA EXCEL
// =====================================================

async function descargarExcelFiltrado(){

    try{

        // =====================================
        // VALIDACION
        // =====================================

        if(
            datosFiltrados.length === 0
        ){

            alert(
                "No hay datos para exportar."
            );

            return;

        }

        actualizarStatusSistema(
            "Generando Excel..."
        );

        // =====================================
        // PAYLOAD
        // =====================================

        const payload = {

            reporte:
                datosFiltrados,

            clientes:
                clientesFiltrados

        };

        // =====================================
        // API
        // =====================================

        const response =
        await fetch(

            "/descargar-filtrado",

            {
                method:"POST",

                headers:{
                    "Content-Type":
                    "application/json"
                },

                body:JSON.stringify(
                    payload
                )
            }

        );

        if(
            !response.ok
        ){

            const errorPayload = await response.json().catch(() => ({}));
            throw new Error(errorPayload.detail || "Error generando Excel.");

        }

        // =====================================
        // ARCHIVO
        // =====================================

        const blob =
        await response.blob();

        const url =
        window.URL.createObjectURL(
            blob
        );

        const a =
        document.createElement(
            "a"
        );

        a.href = url;

        a.download =
        "Reporte_Afluencia_GAC_Filtrado.xlsx";

        document.body.appendChild(
            a
        );

        a.click();

        a.remove();

        window.URL.revokeObjectURL(
            url
        );

        // =====================================
        // STATUS
        // =====================================

        actualizarStatusSistema(

            "Excel descargado correctamente"

        );

    }

    catch(error){

        console.error(
            error
        );

        actualizarStatusSistema(

            "Error al descargar Excel"

        );

        alert(

            error.message

        );

    }

}


document.getElementById("themeToggle").addEventListener("click", alternarTema);
document.getElementById("selectProspectosButton").addEventListener("click", () => document.getElementById("prospectosFile").click());
document.getElementById("selectOportunidadesButton").addEventListener("click", () => document.getElementById("oportunidadesFile").click());
document.getElementById("selectEventosButton").addEventListener("click", () => document.getElementById("eventosFile").click());
document.getElementById("processButton").addEventListener("click", procesarInformacion);
document.getElementById("selectAllVendors").addEventListener("click", seleccionarTodos);
document.getElementById("clearVendorSelection").addEventListener("click", limpiarSeleccion);
document.getElementById("filterButton").addEventListener("click", filtrarTabla);
document.getElementById("downloadButton").addEventListener("click", descargarExcelFiltrado);