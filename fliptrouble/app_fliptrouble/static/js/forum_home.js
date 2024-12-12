const commentairesAffiches = new Set(); // Déclarez le Set à l'extérieur de la fonction
$(document).ready(function () {
  $(".toggle-post-body").on("click", function () {
    const postId = $(this).data("post-id");
    const postBody = $(`#postbody-${postId}`);

    if (postBody.length) {
      postBody.slideToggle(); 

      // Basculer l'icône entre flèche montante et descendante
      if ($(this).hasClass("fa-arrow-down")) {
        $(this).removeClass("fa-arrow-down").addClass("fa-arrow-up");
      } else {
        $(this).removeClass("fa-arrow-up").addClass("fa-arrow-down");
      }

      // Ajouter un élément <p> si le post est vide et ne contient aucun <p>
      if (!postBody.find("p").length) {
        postBody.append("<p></p>");
      }
    } else {
      console.error(`Element with ID 'postbody-${postId}' not found.`);
    }
  });
});

const PostContainer = document.getElementById("PostContainer");
let lastPostId = 0; // Variable globale pour stocker le dernier ID de post récupéré

async function get_post_update() {
  const postElement = document.querySelector(".toggle-post-body");
  let last_id = postElement.getAttribute("data-post-id");
  let param = {};

  try {
    const resultats = await envoyerRequeteAjax(
      `/app_fliptrouble/forum/get_posts?lastPostId=${last_id}`,
      "GET"
    );

    if (!resultats || !resultats.posts || resultats.posts.length === 0) {
      console.log("Aucun nouveau post trouvé.");
      return;
    }

    const posts = resultats.posts;

    ajouter_post(posts);
  } catch (error) {
    console.error("Erreur:", error);
  }

  function ajouter_post(posts) {
    posts.forEach((post) => {
      const nouveauPost = `
                <div class="row mb-4">
                    <div class="col-12">
                        <div class="bg-brunpale card shadow-sm h-100 hover-shadow">
                            <div class="row-forum-content">
                                <div class="d-flex align-items-center justify-content-between">
                                    <h4 class="card-title mb-0">
                                        <a href="/app_fliptrouble/forum/${
                                          post.id
                                        }">${post.titre}</a>  
                                    </h4>
                                    <div class="ml-2 text-right">
                                        <p class="card-text mb-0"><small>Auteur:</small> ${
                                          post.id_user__username
                                        }</p>
                                        <p class="card-text"><small>Créé à: ${new Date(
                                          post.cree_a
                                        ).toLocaleString()}</small></p>
                                    </div>
                                    <div class="ml-3">
                                        <i class="fas fa-arrow-down toggle-post-body" data-post-id="${
                                          post.id
                                        }"></i>
                                    </div>
                                </div>
                            </div>
                            <div class="post-body" id="postbody-${
                              post.id
                            }" style="display: none">
                                ${post.contenu}
                            </div>
                        </div>
                    </div>
                </div>`;
    });
    switch (post.categorie) {
      case 0:
        document.getElementById("category-jeux").prepend(nouveauPost);
        document.getElementById("category-jeux").lastChild?.remove();
        break;
      case 1:
        document.getElementById("category-general").prepend(nouveauPost);
        document.getElementById("category-jeux").lastChild?.remove();

        break;
      case 2:
        document.getElementById("category-humour").prepend(nouveauPost);
        document.getElementById("category-jeux").lastChild?.remove();


        break;
      default:
        console.error("Catégorie inconnue:", post.category);
    }
  }
}
async function chargerPosts(categorie) {
  // je recupere la valeur du dernier post de la categorie
  let last_id = 0;
  console.log("category", categorie);
  console.log("allo");

  // Récupérer l'ID du dernier post dans la catégorie générale
  let divcategory = document.getElementById(`category-${categorie}`);
  const postElements = divcategory.querySelectorAll(".toggle-post-body");

  // Vérifier si des éléments ont été trouvés, puis récupérer le dernier
  if (postElements.length > 0) {
    const lastPostElement = postElements[postElements.length - 1]; // Dernier élément
    last_id = lastPostElement.getAttribute("data-post-id");
    console.log("last_id", last_id);
  } else {
    console.log("Aucun post trouvé dans la catégorie:", categorie);
  }

  try {
    const resultats = await envoyerRequeteAjax(
      `/app_fliptrouble/forum/chargerplus/${last_id}/${categorie}`, 
      "GET"
    );

    if (!resultats || !resultats.posts || resultats.posts.length === 0) {
      console.log("Aucun nouveau post trouvé.");
      return;
    }

    const posts = resultats.posts;
    console.log("posts", posts);

    posts.forEach((post) => {
      const nouveauPost =
      
      `
    <div class="row mb-4">
        <div class="col-12">
          <div class="couleurForum card shadow-sm h-100 hover-shadow">
            <div class="row-forum-content">
              <div class="d-flex align-items-center justify-content-between">
                <h4 class="card-title mb-0">
                  <a href="/app_fliptrouble/forum/${post.id}">${post.titre.substring(0, 50)}</a>
                </h4>
                <div class="d-flex align-items-center">
                  <div class="autheurDate text-right mr-3">
                    <p class="card-text mb-0">Auteur:
                      <strong class="strongUsernname">${post.id_utilisateur}</strong>
                    </p>
                    <p class="card-text">
                      <small>Créé le: ${new Date(post.cree_a).toLocaleString('fr-FR', {
                        day: '2-digit',
                        month: 'short',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}</small>
                    </p>
                  </div>
                  <div>
                    <i class="fas fa-arrow-down toggle-post-body" data-post-id="${post.id}"></i>
                  </div>
                </div>
              </div>
            </div>
            <div class="post-body" id="postbody-${post.id}">
              ${post.contenu}
            </div>
          </div>
        </div>
      </div>`;
  $(`#category-${categorie}`).append(nouveauPost);
});

  } catch (error) {
    console.error("Erreur:", error);
  }
}

async function ajouter_post_forum() {
  let titre = document.getElementById("titre").value;
  let body = document.getElementById("body").value;
  let category = document.getElementById("category").value;
  console.log("csrftoken", csrftoken);
  let param = {
    titre: titre,
    body: body,
    category: category,
  };

  try {
    const resultats = await envoyerRequeteAjax(
      `/app_fliptrouble/forum/ajouter_post`,
      "POST",
      param
    );

    console.log("resultats", resultats);
    if (resultats.status === 200) {
      console.log("Post créé avec succès");
      // Recharger la page pour voir le nouveau post
      window.location.reload();
    } else {
      console.error("Erreur lors de la création du post");
    }
  } catch (error) {
    console.error("Erreur:", error);
  }
}

function initialisation() {
  // Ajouter l'événement click pour le bouton "Charger plus" et le data-category du bouton cliqu//é
  $("#chargerPlus").on("click", () => chargerPosts("general"));
  $("#chargerPlushumour").on("click", () => chargerPosts("humour"));
  $("#chargerPlusJeux").on("click", () => chargerPosts("jeux"));

  let postContainer = document.getElementById("PostContainer");

  if (postContainer) {
    get_post_update(lastPostId);
    setInterval(() => get_post_update(lastPostId), 5000); // 5000ms = 5 secondes
  } else {
    console.error("PostContainer non trouvé");
  }
}
// Lancer la fonction d'initialisation au chargement de la page
window.addEventListener("load", initialisation);
