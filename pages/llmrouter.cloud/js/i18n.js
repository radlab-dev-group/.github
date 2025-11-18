import { translations } from './translations.js';

class I18n {
  constructor() {
    this.currentLang = this.detectLanguage();
    this.translations = translations;
  }

  /**
   * Detects user's preferred language from browser settings
   * Falls back to 'en' if not Polish
   */
  detectLanguage() {
    const savedLang = localStorage.getItem('lang');
    if (savedLang && (savedLang === 'pl' || savedLang === 'en')) {
      return savedLang;
    }

    const browserLang = navigator.language || navigator.userLanguage;
    return browserLang.startsWith('pl') ? 'pl' : 'en';
  }

  /**
   * Gets translation for a key in the current language
   * @param {string} key - Translation key (e.g., 'hero.title')
   * @returns {string} Translated text or key if not found
   */
  t(key) {
    const translation = this.translations[this.currentLang]?.[key];
    if (translation === undefined) {
      console.warn(`Translation missing for key: ${key} in language: ${this.currentLang}`);
      return key;
    }
    return translation;
  }

  /**
   * Changes the current language
   * @param {string} lang - Language code ('pl' or 'en')
   */
  setLanguage(lang) {
    if (lang !== 'pl' && lang !== 'en') {
      console.error(`Invalid language: ${lang}`);
      return;
    }
    this.currentLang = lang;
    localStorage.setItem('lang', lang);
    this.updatePageLanguage();
  }

  /**
   * Gets the current language
   * @returns {string} Current language code
   */
  getLanguage() {
    return this.currentLang;
  }

  /**
   * Updates all elements with data-i18n attribute
   */
  updatePageLanguage() {
    // Update html lang attribute
    document.documentElement.lang = this.currentLang;

    // Update all elements with data-i18n attribute
    document.querySelectorAll('[data-i18n]').forEach(element => {
      const key = element.getAttribute('data-i18n');
      const translation = this.t(key);
      
      if (element.hasAttribute('data-i18n-html')) {
        element.innerHTML = translation;
      } else {
        element.textContent = translation;
      }
    });

    // Update elements with data-i18n-attr (for attributes like aria-label, placeholder, etc.)
    document.querySelectorAll('[data-i18n-attr]').forEach(element => {
      const attrConfig = element.getAttribute('data-i18n-attr');
      const [attr, key] = attrConfig.split(':');
      if (attr && key) {
        element.setAttribute(attr, this.t(key));
      }
    });

    // Dispatch custom event for language change
    window.dispatchEvent(new CustomEvent('languageChanged', { 
      detail: { language: this.currentLang } 
    }));
  }

  /**
   * Initializes i18n after DOM is ready
   */
  init() {
    this.updatePageLanguage();
  }
}

// Create singleton instance
export const i18n = new I18n();
