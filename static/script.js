// Simple form validation
function validateForm() {
    let phone = document.forms["userForm"]["phone"].value;
    let family = document.forms["userForm"]["family_phone"].value;

    if (phone.length != 10 || family.length != 10) {
        alert("Phone numbers must be 10 digits!");
        return false;
    }

    return true;
}

// Confirm before submit
function confirmSubmit() {
    return confirm("Are you sure you want to submit?");
}

// Search filter in dashboard
function searchTable() {
    let input = document.getElementById("search");
    let filter = input.value.toLowerCase();
    let rows = document.querySelectorAll("table tr");

    rows.forEach((row, index) => {
        if (index === 0) return;
        let text = row.innerText.toLowerCase();
        row.style.display = text.includes(filter) ? "" : "none";
    });
}