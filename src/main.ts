import { createApp } from "vue";
import { createVuetify } from "vuetify";
import * as components from "vuetify/components";
import * as directives from "vuetify/directives";
import "vuetify/styles";
import "@mdi/font/css/materialdesignicons.css";
import "@fontsource/dm-sans/400.css";
import "@fontsource/dm-sans/500.css";
import "@fontsource/dm-sans/600.css";
import "@fontsource/dm-sans/700.css";
import "@fontsource/manrope/400.css";
import "@fontsource/manrope/500.css";
import "@fontsource/manrope/600.css";
import "@fontsource/manrope/700.css";
import "./style.css";
import App from "./App.vue";
const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: "mise",
    themes: {
      mise: {
        dark: false,
        colors: {
          primary: "#28483b",
          secondary: "#b76943",
          background: "#f6f5f0",
          surface: "#ffffff",
          error: "#ac3d35",
          success: "#3e7052",
          warning: "#a57027",
        },
      },
    },
  },
  defaults: {
    VBtn: { rounded: "lg", elevation: 0 },
    VTextField: {
      variant: "outlined",
      density: "comfortable",
      color: "primary",
    },
    VSelect: { variant: "outlined", density: "comfortable" },
    VCard: { rounded: "xl", elevation: 0 },
    VDialog: { maxWidth: 560 },
  },
});
createApp(App).use(vuetify).mount("#app");
