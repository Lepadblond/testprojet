function enableEdit() {
    // Montre les champs d'input et le bouton "Enregistrer", cache les éléments de texte
    document.getElementById("emailDisplay").style.display = "none";
    document.getElementById("emailInput").style.display = "inline";
    document.getElementById("sexeDisplay").style.display = "none";
    document.getElementById("sexeInput").style.display = "inline";
    document.getElementById("jeuxPrefereDisplay").style.display = "none";
    document.getElementById("jeuxPrefereInput").style.display = "inline";
    document.getElementById("saveButton").style.display = "inline";
  }
  
  function saveChanges() {
    const email = document.getElementById("emailInput").value;
    const sexe = document.getElementById("sexeInput").value;
    const jeuxPrefere = document.getElementById("jeuxPrefereInput").value;
    const formData = new FormData();
    formData.append("email", email);
    formData.append("sexe", sexe);
    formData.append("jeux_prefere", jeuxPrefere);
    formData.append("csrfmiddlewaretoken", "{{ csrf_token }}");
  
    fetch("{% url 'modifier_profil' user_courant.id %}", {
      method: "POST",
      body: formData
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        // Met à jour les valeurs affichées
        document.getElementById("emailDisplay").textContent = email;
        document.getElementById("sexeDisplay").textContent = sexe;
        document.getElementById("jeuxPrefereDisplay").textContent = jeuxPrefere;
  
        // Cache les champs d'input et le bouton "Enregistrer", montre les éléments de texte
        document.getElementById("emailDisplay").style.display = "inline";
        document.getElementById("emailInput").style.display = "none";
        document.getElementById("sexeDisplay").style.display = "inline";
        document.getElementById("sexeInput").style.display = "none";
        document.getElementById("jeuxPrefereDisplay").style.display = "inline";
        document.getElementById("jeuxPrefereInput").style.display = "none";
        document.getElementById("saveButton").style.display = "none";
      } else {
        alert(data.error || "Une erreur est survenue lors de l'enregistrement.");
      }
    })
    .catch(error => {
      console.error("Error:", error);
      alert("Échec de l'enregistrement des modifications.");
    });
  }