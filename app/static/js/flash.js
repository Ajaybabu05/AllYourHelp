document.addEventListener("DOMContentLoaded", function () {

    const flashMessages = document.querySelectorAll(".flash, .flash-message");

    flashMessages.forEach(function (message) {

        setTimeout(function () {

            message.classList.add("hide");

            setTimeout(function () {
                message.remove();
            }, 400);

        }, 2600);

    });

});