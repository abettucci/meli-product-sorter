const obtenerTextoBusqueda = () => {
    let inputBusqueda = document.querySelector("input.nav-search-input");
    return inputBusqueda ? inputBusqueda.value.trim() : "";
};

let allProducts = [];
let currentOffset = 0;
const chunkSize = 10;
let isLoading = false;

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "obtener_total_publicaciones") {
        total_publicaciones = request.total_publicaciones || 0;
        sendResponse({ status: "success" });
        return true; // Necesario para sendResponse asíncrono
    }
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "obtenerTextoBusqueda") {
        sendResponse({ producto: obtenerTextoBusqueda() });
        return true;
    }
    if (request.action === "reordenarProductos") {
        currentOffset = 0;
        allProducts = [];
        reordenarProductosEnLaPagina(request.reviewFilter);
        sendResponse({ status: "ok" });
        return true;
    }
});

const reordenarProductosEnLaPagina = async (filtroReview) => {
    if (isLoading || currentOffset >= total_publicaciones) return;
    isLoading = true;

    const terminoBusqueda = obtenerTextoBusqueda();
    if (!terminoBusqueda) {
        console.warn("No se encontró término de búsqueda");
        isLoading = false;
        return;
    }

    try {
        function sanitizeForJSON(data) {
            // Caso base: valor nulo o undefined
            if (data === null || data === undefined) {
                return null; // JSON no soporta undefined, lo convertimos a null
            }
        
            // Manejo de números (incluyendo NaN)
            if (typeof data === 'number') {
                return isNaN(data) ? null : data;
            }
        
            // Manejo de strings (verificar si es string vacío)
            if (typeof data === 'string') {
                return data.trim() === '' ? null : data;
            }
        
            // Manejo de booleanos (los dejamos como están)
            if (typeof data === 'boolean') {
                return data;
            }
        
            // Manejo de arrays (aplicamos sanitización recursiva)
            if (Array.isArray(data)) {
                return data.map(item => sanitizeForJSON(item));
            }
        
            // Manejo de objetos (sanitización recursiva de propiedades)
            if (typeof data === 'object') {
                const sanitized = {};
                for (const key in data) {
                    if (data.hasOwnProperty(key)) {
                        sanitized[key] = sanitizeForJSON(data[key]);
                    }
                }
                return sanitized;
            }
        
            // Para cualquier otro tipo no contemplado, devolvemos null
            return null;
        }

        const fetchData = async (terminoBusqueda, chunkSize, currentOffset, extraData = {}) => {
            const requestData = sanitizeForJSON({
                q: terminoBusqueda,
                limit: chunkSize,
                offset: currentOffset,
                ...extraData
            });
        
            try {
                const response = await fetch('https://9baaasalia.execute-api.us-east-2.amazonaws.com/test/productos', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Secure': 'true' 
                    },
                    body: JSON.stringify(requestData)
                });
        
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
                return await response.json();
            } catch (error) {
                console.error('Fetch error:', error);
                throw error;
            }
        };
        
        // Uso:
        const productosLimpios = await fetchData(terminoBusqueda, chunkSize, currentOffset, '');

        allProducts = [...allProducts, ...productosLimpios];        
        const productosOrdenados = ordenarProductos(allProducts, filtroReview);

        renderizarProductos(productosOrdenados);
        
        currentOffset += chunkSize;

        if (productosLimpios.length >= chunkSize) {
            setTimeout(() => reordenarProductosEnLaPagina(filtroReview), 500);
        }

    } catch (error) {
        console.error("Error al reordenar productos:", error);
    } finally {
        isLoading = false;
    }
};

const ordenarProductos = (productos, criterio) => {
    if (criterio === 'promedio_evaluaciones') {
        return [...productos].sort((a, b) => {
            // Primero comparar por cantidad de reviews (descendente)
            const diffReviews = (b.total_reviews || 0) - (a.total_reviews || 0);
            
            // Si tienen la misma cantidad de reviews, comparar por rating promedio (descendente)
            if (diffReviews === 0) {
                return (b.rating_average || 0) - (a.rating_average || 0);
            }
            
            return diffReviews;
        });
    }
    
    // Ordenar por categoría específica
    return [...productos].sort((a, b) => {
        const ratingA = obtenerRatingCategoria(a.review_attributes, criterio);
        const ratingB = obtenerRatingCategoria(b.review_attributes, criterio);
        return ratingB - ratingA;
    });
};

const obtenerRatingCategoria = (reviewAttributes, categoria) => {
    if (!reviewAttributes || !Array.isArray(reviewAttributes)) return 0;
    const categoriaAttr = reviewAttributes.find(attr => attr.display_text === categoria);
    return categoriaAttr ? categoriaAttr.average_rating : 0;
};

const renderizarProductos = (productos) => {
    const contenedor = document.querySelector("ol.ui-search-layout");
    if (!contenedor) return;
    
    // Limpiar solo en la primera carga
    if (currentOffset === chunkSize) {
        contenedor.innerHTML = "";
    }
    
    productos.slice(currentOffset - chunkSize, currentOffset).forEach(producto => {
        const formatPrice = (price) => {
            return '$' + Number(price || 0).toLocaleString('es-AR', {
                minimumFractionDigits: 0,  // Ya está configurado para 0 decimales
                maximumFractionDigits: 0   // Forzamos a 0 decimales
            });
        };
        
        // Generar información de cuotas solo si quantity_cuotas es mayor a 0
        const cuotasInfo = producto.quantity_cuotas > 0 ? `
            <div class="ui-search-reviews" style="margin-top: 4px;">
                <span class="ui-search-reviews__rating">o en ${producto.quantity_cuotas} cuotas de ${formatPrice(producto.sale_price_per_cuota)}</span>
            </div>
        ` : '';
    
        const itemHTML = `
        <li class="ui-search-layout__item shops__layout-item">
            <div style="display: contents;">
                <div class="ui-search-result__wrapper">
                    <div class="andes-card ui-search-result ui-search-result--core andes-card--flat andes-card--padding-16">
                        <div class="ui-search-result__image">
                            <img src="${getHighResImageUrl(producto.portada)}" 
                                alt="${producto.titulo}" 
                                class="ui-search-result-image__element">
                        </div>
                        <div class="ui-search-result__content-wrapper">        
                            <a href="${producto.item_url}" class="ui-search-item__group__element ui-search-link" target="_blank">
                                <h2 class="ui-search-item__title">${producto.titulo}</h2>
                            </a>
                            
                            <div class="ui-search-reviews">
                                ${producto.total_reviews > 0 ? `
                                    <span class="ui-search-reviews__amount">${producto.rating_average?.toFixed(1)}</span>
                                    <span class="ui-search-reviews__stars" style="color: #3483fa !important;">${'★'.repeat(Math.round(producto.rating_average))}${'☆'.repeat(5 - Math.round(producto.rating_average))}</span>                                    <span class="ui-search-reviews__amount">(${producto.total_reviews})</span>
                                ` : ''}
                            </div>
                            
                            <div class="ui-search-price">
                                <span class="ui-search-price__part">${formatPrice(producto.sale_price)}</span>
                            </div>
    
                            ${cuotasInfo}
                            
                            <div class="ui-search-item__shipping">
                                ${producto.seller_nickname ? `<div class="ui-search-item__location">Vendido por <strong>${producto.seller_nickname}</strong></div>` : ''}
                                ${producto.free_shipping ? '<span class="ui-search-item__shipping--free">Envío gratis</span>' : ''}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </li>
        `;
        
        contenedor.insertAdjacentHTML("beforeend", itemHTML);

        // Función para obtener imagen en alta resolución
        function getHighResImageUrl(originalUrl) {
            if (!originalUrl) return '';
            
            // Si ya es una URL de ML con parámetros, la devolvemos tal cual
            if (originalUrl.includes('D_NQ_NP')) return originalUrl;
            
            // Si es una URL básica, intentamos construir una mejor
            try {
                const url = new URL(originalUrl);
                // Para imágenes de ML, podemos forzar mayor calidad con parámetros
                if (url.hostname.includes('mercadolibre') || url.hostname.includes('mlstatic.com')) {
                    return originalUrl.replace('http:', 'https:') + '?format=webp&quality=85';
                }
                return originalUrl;
            } catch {
                return originalUrl;
            }
        }

    });


    // productos.forEach(producto => {
    //     // Validar que los datos existen antes de usarlos
    //     const url = producto.item_url || "#";
    //     const portada = producto.portada || "https://via.placeholder.com/150";
    //     const titulo = producto.titulo || "Producto sin título";
    //     const sale_price = producto.sale_price ? `$${producto.sale_price}` : "Precio no disponible";
    //     const rating_average = producto.rating_average !== undefined ? `⭐ ${producto.rating_average}` : "⭐ N/A";
    //     const seller = producto.seller_nickname || "Producto sin vendedor";
    //     const total_reviews = producto.total_reviews || "Sin reseñas";

    //     let item = document.createElement("li");
    //     item.classList.add("ui-search-layout__item");
    //     item.innerHTML = `
    //         <div class="ui-search-result">
    //             <a href="${url}" target="_blank" class="poly-component__title">
    //                 <img src="${portada}" alt="${titulo}" style="width:150px; height:150px;">
    //                 <h3>${titulo}</h3>
    //             </a>
    //             <h3>${seller}</h3>
    //             <p class="rating">Avg rating: ${rating_average}</p>
    //             <p class="rating">Reviews: ${total_reviews}</p>
    //             <p class="price">${sale_price}</p>
    //         </div>
    //     `;

    //     contenedor.appendChild(item);
    // });

};

const toggleLoadMoreButton = (mostrar) => {
    let boton = document.getElementById('load-more-extension');
    
    if (mostrar) {
        if (!boton) {
            boton = document.createElement('button');
            boton.id = 'load-more-extension';
            boton.textContent = 'Cargar más productos';
            boton.style.cssText = `
                display: block;
                margin: 20px auto;
                padding: 10px;
                background: #3483fa;
                color: white;
                border: none;
                cursor: pointer;
            `;
            boton.onclick = () => reordenarProductosEnLaPagina();
            document.body.appendChild(boton);
        }
    } else if (boton) {
        boton.remove();
    }
};