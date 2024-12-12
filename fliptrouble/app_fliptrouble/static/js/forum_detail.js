$(document).ready(function () {
  // Afficher ou cacher le formulaire principal
  $("#afficher-formulaire").on("click", function () {
    const formulaire = $("#ajout-commentaire");
    formulaire.toggle(); // Utilise toggle() pour simplifier
  });

  // Gérer l'affichage du formulaire de réponse pour chaque bouton "Répondre"
  $(".btn-repondre").on("click", function (event) {
    event.preventDefault();

    // Récupérer l'ID du commentaire parent
    const parentId = $(this).data("id");

    // Trouver le formulaire de réponse correspondant
    const commentaireContainer = $(this).closest(".commentaireContainer");
    const form = commentaireContainer.find("#ajouterCommentaireEnfant");

    // Afficher ou cacher le formulaire
    form.toggle();

    // Mettre à jour l'input caché avec l'ID du parent
    form.find("input[name='parent_id']").val(parentId);
  });
  // Afficher ou cacher les réponses
  $(".btn-masquer-reponses").on("click", function (event) {
    event.preventDefault();

    // Récupérer l'ID du commentaire
    const commentaireId = $(this).data("id");

    // Trouver le conteneur des réponses correspondant
    const reponsesContainer = $(`#reponses-${commentaireId}`);

    // Basculer la visibilité
    reponsesContainer.toggle();

    // Modifier le texte du lien en fonction de l'état
    const lien = $(this);
    if (reponsesContainer.is(":visible")) {
      lien.text("Masquer les réponses");
    } else {
      lien.text("Afficher les réponses");
    }
  });
});
