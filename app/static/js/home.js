const searchButton = document.getElementById("searchButton");
const serviceSearch = document.getElementById("serviceSearch");

if (searchButton && serviceSearch) {

    searchButton.addEventListener("click", function () {

        const searchTerm = serviceSearch.value.trim();

        if (searchTerm === "") {
            alert("Please enter a service you are looking for.");
            return;
        }

        alert(
            "Search functionality will be connected when we build the Services page."
        );

    });

}


const menuToggle = document.getElementById("menuToggle");

const navLinks = document.querySelector(".nav-links");

if (menuToggle && navLinks) {

    menuToggle.addEventListener("click", function () {

        navLinks.classList.toggle("mobile-active");

    });

}

document.addEventListener("DOMContentLoaded", function () {

    const flashMessages = document.querySelectorAll(".flash");

    flashMessages.forEach(function (message) {

        setTimeout(function () {

            message.classList.add("hide");

            setTimeout(function () {
                message.remove();
            }, 400);

        }, 2600);

    });

});