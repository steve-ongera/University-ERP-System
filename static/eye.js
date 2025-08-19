document.getElementById('togglePassword').addEventListener('click', function () {
    const passwordField = document.getElementById('password');
    const icon = document.getElementById('togglePassword');
  
    // Toggle the type of the password field between 'password' and 'text'
    if (passwordField.type === 'password') {
      passwordField.type = 'text'; // Change type to text to show password
      icon.classList.remove('bi-eye-slash'); // Change icon to eye
      icon.classList.add('bi-eye'); 
    } else {
      passwordField.type = 'password'; // Change type back to password to hide password
      icon.classList.remove('bi-eye'); // Change icon to eye-slash
      icon.classList.add('bi-eye-slash');
    }
  });




  
  
  // Toggle Password visibility for "Confirm Password" field
  document.getElementById('togglePassword2').addEventListener('click', function () {
    const confirmPasswordField = document.getElementById('password2');
    const icon = document.getElementById('togglePassword2');
  
    if (confirmPasswordField.type === 'password') {
      confirmPasswordField.type = 'text';
      icon.classList.remove('bi-eye-slash');
      icon.classList.add('bi-eye');
    } else {
      confirmPasswordField.type = 'password';
      icon.classList.remove('bi-eye');
      icon.classList.add('bi-eye-slash');
    }
  });
  
  