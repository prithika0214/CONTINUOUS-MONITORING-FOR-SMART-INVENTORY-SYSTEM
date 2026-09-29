const API = "http://127.0.0.1:5000/api";

async function login() {

    const username =
        document.getElementById("username").value;

    const password =
        document.getElementById("password").value;

    const response = await fetch(`${API}/login`, {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            username: username,
            password: password
        })
    });

    const data = await response.json();

    if (data.success) {

        localStorage.setItem(
            "user_id",
            data.user_id
        );

        localStorage.setItem(
            "username",
            data.name
        );

        localStorage.setItem(
            "role",
            data.role
        );

        if (data.role === "admin") {

            window.location.href =
                "admin/admin.html";

        } else {

            window.location.href =
                "user/user.html";
        }

    } else {

        document.getElementById("message").innerText =
            "Invalid username or password";
    }
}