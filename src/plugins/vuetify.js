import Vue from 'vue';
import Vuetify from 'vuetify/lib';

Vue.use(Vuetify);

export default new Vuetify({
	theme: {
		themes: {
			light: {
				primary: '#009688',
				secondary: '#795548',
				accent: '#ffc107',
				error: '#f44336',
				warning: '#ff5722',
				info: '#03a9f4',
				success: '#8bc34a',
			},

			dark: {

			}
		}
	}
});
