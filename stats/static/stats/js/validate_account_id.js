const form = document.querySelector("form")
const accountIdInput = document.getElementById("id_account_id")

function trim(s) {
    if (s == null)
        return '';
    while (s.substring(0, 1) === ' ') {
        s = s.substring(1, s.length);
    }
    while (s.substring(s.length - 1, s.length) === ' ') {
        s = s.substring(0, s.length - 1);
    }
    return s;
}

function showErrorMessage(message) {
    const td = accountIdInput.parentElement
    const ul = document.createElement("ul")
    const li = document.createElement("li")
    for (const ulChild of td.querySelectorAll("ul")) {
        td.removeChild(ulChild)
    }
    ul.classList.add("errorlist")
    li.innerText = message;
    ul.append(li)
    td.prepend(ul)
}

function checkAccountId() {
    const value = trim(accountIdInput.value);
    if (value.length === 0) {
        showErrorMessage("Wpisz ID konta!");
        accountIdInput.focus();
        return false;
    }

    if (!/^\d+$/.test(value)) {
        showErrorMessage("ID konta musi być liczbą!");
        accountIdInput.focus();
        return false;
    }

    if (parseInt(value) < 1) {
        showErrorMessage("ID konta musi być większe od 0!");
        accountIdInput.focus();
        return false;
    }
    return true;
}

accountIdInput.onchange = checkAccountId;
form.onsubmit = () => {
    return checkAccountId(accountIdInput);
};
