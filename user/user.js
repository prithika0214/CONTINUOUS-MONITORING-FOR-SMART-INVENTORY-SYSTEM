const API =
    "http://127.0.0.1:5000/api";

const userId =
    localStorage.getItem("user_id");


// User protection
if (localStorage.getItem("role") !== "user") {

    window.location.href =
        "../index.html";
}


// Sections
function show(id) {

    document.querySelectorAll("main section")
        .forEach(section => {

            section.classList.add("hidden");

        });

    document.getElementById(id)
        .classList.remove("hidden");

    if (id === "products")
        loadProducts();

    if (id === "requests")
        loadRequests();
}


// Load products
async function loadProducts() {

    const response =
        await fetch(`${API}/user/products`);

    const products =
        await response.json();

    displayProducts(products);
}


// Display products
function displayProducts(products) {

    const container =
        document.getElementById(
            "productList"
        );

    container.innerHTML = "";

    products.forEach(product => {

        container.innerHTML += `

        <div class="product">

            <h3>
                ${product.product_name}
            </h3>

            <p>
                Category:
                ${product.category}
            </p>

            <p>
                Available:
                ${product.quantity}
            </p>

            <p>
                Price:
                ₹${product.price}
            </p>

            <button
                onclick="requestStock(${product.id})">

                Request Stock

            </button>

        </div>

        `;
    });
}


// Search
async function searchProducts() {

    const value =
        document.getElementById(
            "search"
        ).value.toLowerCase();

    const response =
        await fetch(`${API}/user/products`);

    const products =
        await response.json();

    const filtered =
        products.filter(product =>
            product.product_name
                .toLowerCase()
                .includes(value)
        );

    displayProducts(filtered);
}


// Request stock
async function requestStock(productId) {

    const quantity =
        prompt("Enter required quantity:");

    if (!quantity)
        return;

    const reason =
        prompt("Enter reason:");

    const response =
        await fetch(`${API}/requests`, {

            method: "POST",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body: JSON.stringify({

                user_id: userId,

                product_id: productId,

                quantity:
                    Number(quantity),

                reason: reason

            })
        });

    const data =
        await response.json();

    alert(data.message);
}


// User requests
async function loadRequests() {

    const response =
        await fetch(
            `${API}/requests/user/${userId}`
        );

    const requests =
        await response.json();

    const container =
        document.getElementById(
            "requestList"
        );

    container.innerHTML = "";

    requests.forEach(request => {

        container.innerHTML += `

        <div class="product">

            <h3>
                ${request.product_name}
            </h3>

            <p>
                Quantity:
                ${request.quantity}
            </p>

            <p>
                Status:
                ${request.status}
            </p>

            <p>
                Reason:
                ${request.reason}
            </p>

        </div>

        `;
    });
}


// Logout
function logout() {

    localStorage.clear();

    window.location.href =
        "../index.html";
}