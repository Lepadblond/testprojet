// notifications.js

document.addEventListener('DOMContentLoaded', function() {
  const notificationBell = document.getElementById('notification-icon');
  const notificationList = document.getElementById('notification-list');
  const notificationCount = document.getElementById('notification-count');
  let isMenuOpen = false;
  let timeoutId;

  if (notificationBell) {
      notificationBell.addEventListener('mouseover', function(event) {
          event.preventDefault();
          clearTimeout(timeoutId);
          notificationList.style.display = 'block';
          isMenuOpen = true;
      });

      notificationBell.addEventListener('mouseout', function(event) {
          event.preventDefault();
          timeoutId = setTimeout(function() {
              if (!notificationList.matches(':hover')) {
                  notificationList.style.display = 'none';
                  isMenuOpen = false;
              }
          }, 200);
      });

      notificationList.addEventListener('mouseover', function(event) {
          clearTimeout(timeoutId);
          isMenuOpen = true;
      });

      notificationList.addEventListener('mouseout', function(event) {
          timeoutId = setTimeout(function() {
              if (!notificationBell.matches(':hover')) {
                  notificationList.style.display = 'none';
                  isMenuOpen = false;
              }
          }, 200);
      });
  }

  const username = "{{ user.username|escapejs }}";
  if (username) {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const notificationSocket = new WebSocket(protocol + "//" + window.location.host + "/ws/notifications/" + username + "/");

      notificationSocket.onmessage = function(e) {
          const data = JSON.parse(e.data);
          console.log("Received data via WebSocket:", data);

          if (data.type === "notification" || data.type === "send_notification") {
              const notificationItem = document.createElement("div");
              notificationItem.classList.add("dropdown-item", "notif-item");

              let innerHTML = `<span>${data.notification}</span>`;
              if (data.request_id) {
                  innerHTML += `
                      <button class="accept-request" data-request-id="${data.request_id}">Accepter</button>
                      <button class="reject-request" data-request-id="${data.request_id}">Refuser</button>
                  `;
              }
              notificationItem.innerHTML = innerHTML;
              notificationContainer.appendChild(notificationItem);

              let count = parseInt(notificationCount.textContent) || 0;
              count++;
              notificationCount.textContent = count;
              notificationCount.style.display = "block";
          }
      };

      notificationSocket.onclose = function(e) {
          console.error("Le WebSocket de notification s'est fermé de manière inattendue");
      };
  } else {
      console.error("Username not found or user not authenticated");
  }

  document.addEventListener('click', function(event) {
      if (event.target.classList.contains('accept-request') || event.target.classList.contains('reject-request')) {
          const requestId = event.target.dataset.requestId;
          const isAccept = event.target.classList.contains('accept-request');
          const url = isAccept ? `/app_fliptrouble/accept_friend_request/${requestId}/` : `/app_fliptrouble/decline_friend_request/${requestId}/`;

          fetch(url, {
              method: "POST",
              headers: {
                  "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
              },
          })
          .then(response => response.json())
          .then(data => {
              console.log(data.message);
              const btn = event.target;
              const notifItem = btn.closest('.notif-item');
              if (notifItem) {
                  notifItem.remove();
              }

              let count = parseInt(notificationCount.textContent) || 0;
              if (count > 0) {
                  count--;
                  notificationCount.textContent = count;
                  if (count === 0) {
                      notificationCount.style.display = "none";
                      if (notificationContainer.children.length === 0) {
                          notificationContainer.innerHTML = '<p class="dropdown-item text-muted">Aucune notification</p>';
                      }
                  }
              }
          })
          .catch(error => console.error("Error:", error));
      }
  });
});
