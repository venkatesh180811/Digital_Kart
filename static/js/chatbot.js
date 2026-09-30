(function() {
  'use strict';

  function getCookie(name) {
    const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    if (match) return match[2];
    return '';
  }

  const CSRF_TOKEN = getCookie('csrftoken');
  const CHAT_API_URL = '/chatbot/api/chat/';

  function getEl(id) {
    return document.getElementById(id);
  }

  function scrollToBottom() {
    const messages = getEl('dk-chatbot-messages');
    if (messages) {
      messages.scrollTop = messages.scrollHeight;
    }
  }

  function formatTime() {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  function appendMessage(role, text) {
    const container = getEl('dk-chatbot-messages');
    if (!container) return;

    const wrapper = document.createElement('div');
    wrapper.className = `dk-chatbot-message ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'dk-chatbot-avatar';
    avatar.innerHTML = role === 'assistant' ? '<i class="fa-solid fa-robot"></i>' : '<i class="fa-solid fa-user"></i>';

    const bubble = document.createElement('div');
    bubble.className = 'dk-chatbot-bubble';

    const content = document.createElement('div');
    content.className = 'dk-chatbot-text';
    content.textContent = text;

    const time = document.createElement('div');
    time.className = 'dk-chatbot-time';
    time.textContent = formatTime();

    bubble.appendChild(content);
    bubble.appendChild(time);
    wrapper.appendChild(avatar);
    wrapper.appendChild(bubble);
    container.appendChild(wrapper);
    scrollToBottom();
  }

  function appendProductCards(products) {
    const container = getEl('dk-chatbot-products');
    if (!container || !products || !products.length) return;

    container.innerHTML = '';
    products.forEach(product => {
      const card = document.createElement('a');
      card.className = 'dk-chatbot-product-card';
      card.href = product.url || '#';
      card.target = '_self';

      const imageWrap = document.createElement('div');
      imageWrap.className = 'dk-chatbot-product-image';
      if (product.image) {
        const img = document.createElement('img');
        img.src = product.image;
        img.alt = product.name;
        imageWrap.appendChild(img);
      } else {
        imageWrap.innerHTML = '<i class="fa-solid fa-image" style="color:var(--text-400);opacity:0.5;"></i>';
      }

      const info = document.createElement('div');
      info.className = 'dk-chatbot-product-info';

      const name = document.createElement('div');
      name.className = 'dk-chatbot-product-name';
      name.textContent = product.name;

      const price = document.createElement('div');
      price.className = 'dk-chatbot-product-price';
      price.textContent = '₹' + Number(product.price).toLocaleString('en-IN');

      info.appendChild(name);
      info.appendChild(price);
      card.appendChild(imageWrap);
      card.appendChild(info);
      container.appendChild(card);
    });
  }

  function setTyping(show) {
    const el = getEl('dk-chatbot-typing');
    if (el) {
      el.style.display = show ? 'flex' : 'none';
    }
    scrollToBottom();
  }

  async function sendMessage(message) {
    if (!message || !message.trim()) return;

    const input = getEl('dk-chatbot-input');
    if (input) input.value = '';

    appendMessage('user', message.trim());
    setTyping(true);

    try {
      const response = await fetch(CHAT_API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': CSRF_TOKEN,
        },
        body: JSON.stringify({ message: message.trim() }),
      });

      setTyping(false);

      if (!response.ok) {
        const data = await response.json();
        appendMessage('assistant', data.message || 'Sorry, something went wrong. Please try again.');
        return;
      }

      const data = await response.json();
      if (data.message) {
        appendMessage('assistant', data.message);
      }
      if (data.products && data.products.length) {
        appendProductCards(data.products);
      }
    } catch (error) {
      setTyping(false);
      appendMessage('assistant', 'Sorry, I\'m having trouble connecting right now. Please try again.');
    }
  }

  function initChatbot() {
    const toggle = getEl('dk-chatbot-toggle');
    const close = getEl('dk-chatbot-close');
    const window_ = getEl('dk-chatbot-window');
    const form = getEl('dk-chatbot-form');
    const input = getEl('dk-chatbot-input');

    if (!toggle || !window_) return;

    toggle.addEventListener('click', () => {
      const isOpen = window_.classList.contains('open');
      if (isOpen) {
        window_.classList.remove('open');
        window_.setAttribute('aria-hidden', 'true');
        toggle.innerHTML = '<i class="fa-solid fa-comments"></i>';
      } else {
        window_.classList.add('open');
        window_.setAttribute('aria-hidden', 'false');
        toggle.innerHTML = '<i class="fa-solid fa-xmark"></i>';
        if (input) setTimeout(() => input.focus(), 150);
      }
    });

    if (close) {
      close.addEventListener('click', () => {
        window_.classList.remove('open');
        window_.setAttribute('aria-hidden', 'true');
        toggle.innerHTML = '<i class="fa-solid fa-comments"></i>';
      });
    }

    if (form) {
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        const text = input?.value || '';
        sendMessage(text);
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initChatbot);
  } else {
    initChatbot();
  }
})();
