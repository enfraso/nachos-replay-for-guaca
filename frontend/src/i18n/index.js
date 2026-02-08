/**
 * Nachos Replay - Vue I18n Configuration
 */
import { createI18n } from 'vue-i18n'
import ptBR from './locales/pt-BR.json'
import en from './locales/en.json'

const i18n = createI18n({
    legacy: false,
    locale: localStorage.getItem('locale') || 'pt-BR',
    fallbackLocale: 'en',
    messages: {
        'pt-BR': ptBR,
        'en': en
    }
})

export default i18n
