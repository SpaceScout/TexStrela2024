function showModal(hideMenu) {
  const tagModal = $('#TagModal');
  if (tagModal.length) {
    tagModal.on('shown.bs.modal', hideMenu); // Скрываем контекстное меню после открытия модального окна
    tagModal.modal('show'); // Показываем модальное окно с id "TagModal"
  } else {
    console.error('Tag modal not found');
  }
}

const attachContextMenu = (() => {
  const contextMenu = document.createElement('ul');
  const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;

  const hideOnResize = () => hideMenu(true);

  // Обработчик события для открытия модального окна
  $(document).ready(function() {
    const tagForm = document.forms['tag_form'];

    // Добавляем обработчик события для отправки формы
    tagForm.addEventListener('submit', function(event) {
      event.preventDefault(); // Отменяем стандартное поведение отправки формы

      // Получаем значение тега из поля ввода
      const tagValue = tagForm.elements['tag'].value;

      // Получаем значение photoId из скрытого поля
      const photoId = tagForm.elements['photo_id'].value;
      console.log("PhotoId from form:", photoId); // Отладочное сообщение

      // Отправляем данные на сервер
      fetch(`/tags/add-tag/?tag=${tagValue}&file_id=${photoId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
      })
      .then(response => {
        if (response.ok) {
          console.log(`Tag ${tagValue} successfully added to photo ${photoId}`);
          window.location.reload();
        } else {
          console.error(`Failed to add tag ${tagValue} to photo ${photoId}`);
        }
      })
      .catch(error => console.error('Error:', error));

      $('#TagModal').modal('hide'); // Закрываем модальное окно
    });
  });

  function hideMenu(e) {
    if (e === true || !contextMenu.contains(e.target)) {
      contextMenu.remove();
      document.removeEventListener('click', hideMenu);
      window.removeEventListener('resize', hideOnResize);
    }
  };

  const attachOption = (target, opt, photoId) => {
    const item = document.createElement('li');
    item.className = 'context-menu-item';
    item.innerHTML = `<span>${opt.label}</span>`;
    item.addEventListener('click', e => {
      e.stopPropagation();
      if (!opt.subMenu || opt.subMenu.length === 0) {
        opt.action(opt);
        hideMenu(true);
      }
    });

    target.appendChild(item);

    if (opt.subMenu && opt.subMenu.length) {
      const subMenu = document.createElement('ul');
      subMenu.className = 'context-sub-menu';
      item.appendChild(subMenu);
      opt.subMenu.forEach(subOpt => attachOption(subMenu, subOpt, photoId))
    }
  };

  const showMenu = (e, menuOptions) => {
    e.preventDefault();
    contextMenu.className = 'context-menu';
    contextMenu.innerHTML = '';
    const photoId = e.currentTarget.dataset.photoId; // Получаем photoId из контекстного меню
    const tagForm = document.forms['tag_form']; // Получаем форму
    // Устанавливаем значение поля photo_id в форме
    tagForm.elements['photo_id'].value = photoId;
    menuOptions.forEach(opt => attachOption(contextMenu, opt, photoId))
    document.body.appendChild(contextMenu);

    const { innerWidth, innerHeight } = window;
    const { offsetWidth, offsetHeight } = contextMenu;
    let x = 0;
    let y = 0;

    if (e.clientX >= (innerWidth / 2)) {
      contextMenu.classList.add('left');
    }

    if (e.clientY >= (innerHeight / 2)) {
      contextMenu.classList.add('top');
    }

    if (e.clientX >= (innerWidth - offsetWidth)) {
      x = '-100%';
    }

    if (e.clientY >= (innerHeight - offsetHeight)) {
      y = '-100%';
    }

    contextMenu.style.left = e.clientX + 'px';
    contextMenu.style.top = e.clientY + 'px';
    contextMenu.style.transform = `translate(${x}, ${y})`;
    document.addEventListener('click', hideMenu);
    window.addEventListener('resize', hideOnResize);
  };

  return (el, options) => {
    el.addEventListener('contextmenu', (e) => {
      const photoId = e.currentTarget.dataset.photoId;
      console.log("PhotoId from context menu:", photoId); // Отладочное сообщение
      showMenu(e, options.map(opt => ({ ...opt, photoId })));
    });
  };
})();

document.querySelectorAll('.card')
  .forEach(btn => {
    attachContextMenu(btn, [
      {
        label: "Delete",
        action(opt) {
          const photoId = opt.photoId;
          const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
          console.log(csrfToken)
          fetch(`/delete/${photoId}/`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': csrfToken,
            },
          })
          .then(response => {
            if (response.ok) {
              console.log(`Photo ${photoId} successfully deleted`);
              window.location.reload();
            } else {
              console.error(`Failed to delete photo ${photoId}`);
            }
          })
          .catch(error => console.error('Error:', error));
        },
      },
      {
        label: "Save",
        action(opt) {
          const photoId = opt.photoId;
          const csrfToken = opt.csrfToken;
          window.location.href = `/download/${photoId}/`;
        },
      },
        {
          label: "Add tag",
          action(opt) {
            const { photoId, csrfToken, hideMenu } = opt;
            const tagModal = $('#TagModal');
            tagModal.find('input[name="photo_id"]').val(photoId); // Устанавливаем значение photo_id в форме
            showModal(hideMenu); // Передаем функцию hideMenu в showModal
          },
        }
    ]);
  });