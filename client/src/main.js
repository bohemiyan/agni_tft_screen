/*!
 * s1panel-gui - main.js (optimized)
 * Only registers components actually used in the app.
 */

import './assets/theme.css';
import 'primeicons/primeicons.css';
import 'primevue/resources/themes/lara-dark-indigo/theme.css';

import { createApp } from 'vue';
import App from './App.vue';

import PrimeVue          from 'primevue/config';
import ConfirmPopup      from 'primevue/confirmpopup';
import ConfirmationService from 'primevue/confirmationservice';
import FileUpload        from 'primevue/fileupload';
import Tooltip           from 'primevue/tooltip';

import RectEdit from '@/components/RectEdit.vue';
import FontEdit from '@/components/FontEdit.vue';

const app = createApp(App);

app.use(PrimeVue, { ripple: true, inputStyle: 'outlined' });
app.use(ConfirmationService);

app.directive('Tooltip', Tooltip);

app.component('ConfirmPopup',  ConfirmPopup);
app.component('FileUpload',    FileUpload);
app.component('RectEdit',      RectEdit);
app.component('FontEdit',      FontEdit);

app.mount('#app');
