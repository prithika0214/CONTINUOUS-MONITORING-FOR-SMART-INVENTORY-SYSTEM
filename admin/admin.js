const API =
    "http://127.0.0.1:5000/api";


// Security check for interface
if (localStorage.getItem("role") !== "admin") {

    window.location.href =
        "../index.html";
}


// Show section
function showSection(id) {

    document.querySelectorAll("main section")
        .forEach(section => {

            section.classList.add("hidden");

        });

    document.getElementById(id)
        .classList.remove("hidden");

    if (id === "dashboard")
        loadDashboard();

    if (id === "inventory")
        loadInventory();

    if (id === "alerts")
        loadAlerts();
}


// Dashboard
async function loadDashboard() {

    const response =
        await fetch(`${API}/admin/dashboard`);

    const data =
        await response.json();

    document.getElementById(
        "totalProducts"
    ).innerText = data.total_products;

    document.getElementById(
        "lowStock"
    ).innerText = data.low_stock;

    document.getElementById(
        "outStock"
    ).innerText = data.out_of_stock;

    document.getElementById(
        "inventoryValue"
    ).innerText =
        "₹" + data.inventory_value;
}


// Inventory
async function loadInventory() {

    const response =
        await fetch(`${API}/inventory`);

    const data =
        await response.json();

    const table =
        document.getElementById(
            "inventoryTable"
        );

    table.innerHTML = "";

    data.forEach(product => {

        table.innerHTML += `

        <tr>

            <td>${product.product_name}</td>

            <td>${product.category}</td>

            <td>${product.quantity}</td>

            <td>${product.minimum_stock}</td>

            <td>${product.status}</td>

        </tr>

        `;
    });
}


// Alerts
async function loadAlerts() {

    const response =
        await fetch(`${API}/alerts`);

    const data =
        await response.json();

    const container =
        document.getElementById(
            "alertList"
        );

    container.innerHTML = "";

    data.forEach(alert => {

        container.innerHTML += `

        <div class="card">

            <h3>${alert.product}</h3>

            <p>
                Quantity:
                ${alert.quantity}
            </p>

            <p>
                Status:
                ${alert.status}
            </p>

        </div>

        `;
    });
}


// Continuous monitoring
setInterval(() => {

    loadDashboard();

}, 5000);


// Logout
function logout() {

    localStorage.clear();

    window.location.href =
        "../index.html";
}


loadDashboard();