import { createI18n } from 'vue-i18n'
import ptBR from './pt-BR.json'
import enUS from './en-US.json'

// Get saved locale or detect from browser
function getDefaultLocale() {
    const saved = localStorage.getItem('locale')
    if (saved) return saved

    const browserLang = navigator.language || navigator.userLanguage
    if (browserLang.startsWith('pt')) return 'pt-BR'
    return 'en-US'
}

const i18n = createI18n({
    legacy: false,
    locale: getDefaultLocale(),
    fallbackLocale: 'en-US',
    messages: {
        'pt-BR': ptBR,
        'en-US': enUS
    }
})

export function setLocale(locale) {
    i18n.global.locale.value = locale
    localStorage.setItem('locale', locale)
    document.documentElement.lang = locale
}

export default i18n
