import i18nData from '../i18n.json';
import { readable } from 'svelte/store';
export const i18n = readable(i18nData.fr);