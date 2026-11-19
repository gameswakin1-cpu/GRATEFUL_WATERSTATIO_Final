    function sendMail(){
        let parms = {
            name: document.getElementById("name").value,
            email: document.getElementById("email").value,
            phone: document.getElementById("phone").value,
            message: document.getElementById("message").value
        }
            emailjs.sendForm('service_dh2cecb', 'template_i47jasp',parms).then(alert("Message Sent Successfully"), function(error){
                alert("Failed to send message. Please try again later.");
             });

    }