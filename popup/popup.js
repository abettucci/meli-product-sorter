document.addEventListener("DOMContentLoaded", async () => {
    const reviewFiltersContainer = document.getElementById("review-filters-container");
    const btnReordenar = document.getElementById("btn-reordenar");

    const obtenerTerminoBusqueda = async () => {
        return new Promise((resolve) => {
            chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
                chrome.tabs.sendMessage(
                    tabs[0].id,
                    { action: "obtenerTextoBusqueda" },
                    (response) => resolve(response?.producto || "")
                );
            });
        });
    };

    // Función para obtener categorías de la API
    const obtenerCategoriasDeReviews = async (termino) => {
        if (!termino) return [];
        
        try {
            const endpoint = `https://9baaasalia.execute-api.us-east-2.amazonaws.com/test/get-reviews-filters?producto=${encodeURIComponent(termino)}`;
            const response = await fetch(endpoint);
            const data = await response.json();

            console.log('data: ', data);

            return data;

        } catch (error) {
            console.error("Error obteniendo categorías:", error);
            return [];
        }
    };

    const eliminarTildes = (texto) => {
        return texto.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
      };

    // Función para renderizar los filtros de reviews (actualizada)
    const renderizarFiltrosReviews = (categorias) => {
        reviewFiltersContainer.innerHTML = "";
        
        const label = document.createElement("label");
        label.textContent = "Ordenar productos por:";
        
        const select = document.createElement("select");
        select.id = "review-categoria";
        
        // Opción por defecto (nueva)
        const defaultOption = document.createElement("option");
        defaultOption.value = "promedio_evaluaciones";
        defaultOption.textContent = "Ordenar por evaluaciones promedio";
        defaultOption.selected = true;
        select.appendChild(defaultOption);
        
        // Opción para no ordenar
        const noneOption = document.createElement("option");
        noneOption.value = "";
        noneOption.textContent = "Sin orden especifico";
        select.appendChild(noneOption);
        
        // Opciones de categorías específicas
        categorias.forEach(categoria => {
            const option = document.createElement("option");
            option.value = eliminarTildes(categoria);
            option.textContent = eliminarTildes(categoria);
            select.appendChild(option);
        });
        
        reviewFiltersContainer.appendChild(label);
        reviewFiltersContainer.appendChild(select);
    };

    // Cargar solo filtros de reviews
     const cargarFiltros = async () => {
        reviewFiltersContainer.innerHTML = "<p>Cargando categorias...</p>";
        
        const termino = await obtenerTerminoBusqueda();

        console.log('termino: ', termino);

        const data_categorias = await obtenerCategoriasDeReviews(termino);
        const categorias = data_categorias.nombres_categorias_de_resenas

        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            chrome.tabs.sendMessage(tabs[0].id, {
                action: "obtener_total_publicaciones",
                total_publicaciones : data_categorias.total_publicaciones
            });
        });
        
        if (categorias.length === 0) {
            reviewFiltersContainer.innerHTML = "<p>No se encontraron categorías para este producto</p>";
            return;
        }
        
        renderizarFiltrosReviews(categorias);
    };


    // Modificación en el evento click del botón
    btnReordenar.addEventListener("click", async () => {
        const termino = await obtenerTerminoBusqueda();
        if (!termino) {
            reviewFiltersContainer.innerHTML = "<p>No se encontró término de búsqueda</p>";
            return;
        }

        const select = document.getElementById("review-categoria");
        const filtro = select ? select.value : "promedio_evaluaciones";
        
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            chrome.tabs.sendMessage(tabs[0].id, {
                action: "reordenarProductos",
                reviewFilter: filtro
            });
        });
    });

    cargarFiltros();
});