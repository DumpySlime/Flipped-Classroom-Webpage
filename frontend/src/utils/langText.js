export function getLangText(val, lang = 'en') {
    if (!val) return '';
    if (typeof val === 'object' && !Array.isArray(val)) {
        return val[lang] || val['en'] || Object.values(val)[0] || '';
    }
    return String(val);
}