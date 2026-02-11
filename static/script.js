async function handleLogin(role) {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    const response = await fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
    });

    const result = await response.json();

    if (result.status === "success") {
        alert("Welcome " + result.name + "! Redirecting to " + result.role + " dashboard...");
        // In a real app: window.location.href = "/dashboard";
    } else {
        alert(result.message);
    }
}