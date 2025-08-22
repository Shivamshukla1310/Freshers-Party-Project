
// ==================== static/js/script.js ==================== -->

// Global JavaScript functions for the Fresher's Party website

// Utility functions
const utils = {
  // Show toast notification
  showToast: function (message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} fixed top-4 right-4 z-50 w-auto max-w-sm transform transition-all duration-300 translate-x-full`;
    toast.innerHTML = `
            <span>${message}</span>
            <button class="btn btn-sm btn-ghost" onclick="this.parentElement.remove()">×</button>
        `;

    document.body.appendChild(toast);

    // Slide in
    setTimeout(() => {
      toast.classList.remove('translate-x-full');
    }, 100);

    // Auto remove after 5 seconds
    setTimeout(() => {
      toast.classList.add('translate-x-full');
      setTimeout(() => toast.remove(), 300);
    }, 5000);
  },

  // Format currency
  formatCurrency: function (amount) {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR'
    }).format(amount);
  },

  // Validate email
  isValidEmail: function (email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
  },

  // Validate mobile number
  isValidMobile: function (mobile) {
    const regex = /^[6-9]\d{9}$/;
    return regex.test(mobile.replace(/\s+/g, ''));
  },

  // Copy to clipboard
  copyToClipboard: function (text) {
    navigator.clipboard.writeText(text).then(() => {
      this.showToast('Copied to clipboard!', 'success');
    }).catch(() => {
      this.showToast('Failed to copy', 'error');
    });
  }
};

// Form validation and enhancement
const formHandler = {
  // Enhance form inputs with real-time validation
  enhanceForm: function (formId) {
    const form = document.getElementById(formId);
    if (!form) return;

    const inputs = form.querySelectorAll('input[required]');

    inputs.forEach(input => {
      // Add validation on blur
      input.addEventListener('blur', function () {
        this.validateInput(input);
      }.bind(this));

      // Add validation on input for better UX
      input.addEventListener('input', function () {
        if (input.classList.contains('input-error')) {
          this.validateInput(input);
        }
      }.bind(this));
    });
  },

  // Validate individual input
  validateInput: function (input) {
    const value = input.value.trim();
    let isValid = true;
    let errorMessage = '';

    // Required field check
    if (!value) {
      isValid = false;
      errorMessage = 'This field is required';
    }

    // Specific validation based on input type/name
    if (value) {
      switch (input.type) {
        case 'email':
          if (!utils.isValidEmail(value)) {
            isValid = false;
            errorMessage = 'Please enter a valid email address';
          }
          break;
        case 'tel':
          if (!utils.isValidMobile(value)) {
            isValid = false;
            errorMessage = 'Please enter a valid 10-digit mobile number';
          }
          break;
      }
    }

    // Update UI based on validation
    if (isValid) {
      input.classList.remove('input-error');
      input.classList.add('input-success');
      this.removeErrorMessage(input);
    } else {
      input.classList.remove('input-success');
      input.classList.add('input-error');
      this.showErrorMessage(input, errorMessage);
    }

    return isValid;
  },

  // Show error message for input
  showErrorMessage: function (input, message) {
    this.removeErrorMessage(input);

    const errorDiv = document.createElement('div');
    errorDiv.className = 'text-error text-sm mt-1';
    errorDiv.textContent = message;
    errorDiv.setAttribute('data-error-for', input.name);

    input.parentNode.appendChild(errorDiv);
  },

  // Remove error message for input
  removeErrorMessage: function (input) {
    const existingError = input.parentNode.querySelector(`[data-error-for="${input.name}"]`);
    if (existingError) {
      existingError.remove();
    }
  },

  // Validate entire form
  validateForm: function (formId) {
    const form = document.getElementById(formId);
    if (!form) return false;

    const inputs = form.querySelectorAll('input[required]');
    let isFormValid = true;

    inputs.forEach(input => {
      if (!this.validateInput(input)) {
        isFormValid = false;
      }
    });

    return isFormValid;
  }
};

// Animation helpers
const animations = {
  // Fade in elements when they come into view
  observeElements: function () {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-fade-up');
          observer.unobserve(entry.target);
        }
      });
    }, {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    });

    // Observe all cards and stats
    document.querySelectorAll('.card, .stat').forEach(el => {
      observer.observe(el);
    });
  },

  // Add hover effects to buttons
  enhanceButtons: function () {
    document.querySelectorAll('.btn').forEach(btn => {
      btn.addEventListener('mouseenter', function () {
        this.style.transform = 'translateY(-2px)';
      });

      btn.addEventListener('mouseleave', function () {
        this.style.transform = 'translateY(0)';
      });
    });
  },

  // Loading animation for buttons
  setButtonLoading: function (buttonElement, isLoading) {
    if (isLoading) {
      buttonElement.disabled = true;
      buttonElement.innerHTML = '<span class="loading loading-spinner loading-sm"></span> Processing...';
    } else {
      buttonElement.disabled = false;
      // Restore original text - you might want to store this beforehand
    }
  }
};

// Admin specific functions
const adminUtils = {
  // Auto-refresh dashboard data
  startAutoRefresh: function (interval = 30000) {
    setInterval(() => {
      if (window.location.pathname === '/admin/dashboard') {
        this.refreshStats();
      }
    }, interval);
  },

  // Refresh dashboard statistics
  refreshStats: function () {
    fetch('/admin/stats')
      .then(response => response.json())
      .then(data => {
        // Update stats if endpoint exists
        console.log('Stats refreshed:', data);
      })
      .catch(error => {
        console.error('Error refreshing stats:', error);
      });
  },

  // Export data with loading state
  exportData: function (format = 'csv') {
    const exportBtn = document.querySelector('[data-export]');
    if (exportBtn) {
      animations.setButtonLoading(exportBtn, true);

      // The actual export happens via the backend route
      // This is just for UI feedback
      setTimeout(() => {
        animations.setButtonLoading(exportBtn, false);
        utils.showToast('Export completed!', 'success');
      }, 2000);
    }
  }
};

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
  // Initialize animations
  animations.observeElements();
  animations.enhanceButtons();

  // Enhance forms if they exist
  const forms = ['registrationForm', 'loginForm'];
  forms.forEach(formId => {
    formHandler.enhanceForm(formId);
  });

  // Initialize admin features if on admin pages
  if (window.location.pathname.startsWith('/admin')) {
    adminUtils.startAutoRefresh();
  }

  // Add smooth scrolling to all links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        target.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
      }
    });
  });

  // Add keyboard shortcuts
  document.addEventListener('keydown', function (e) {
    // ESC to close modals
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal.modal-open').forEach(modal => {
        modal.classList.remove('modal-open');
      });
    }

    // Ctrl+Enter to submit forms
    if (e.ctrlKey && e.key === 'Enter') {
      const activeForm = document.querySelector('form:focus-within');
      if (activeForm) {
        activeForm.dispatchEvent(new Event('submit'));
      }
    }
  });

  // Add theme toggle functionality
  const themeToggle = document.querySelector('[data-theme-toggle]');
  if (themeToggle) {
    themeToggle.addEventListener('click', function () {
      const currentTheme = document.documentElement.getAttribute('data-theme');
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('theme', newTheme);
    });

    // Load saved theme
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
  }

  console.log('🎉 Fresher\'s Party website initialized successfully!');
});