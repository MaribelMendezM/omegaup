<template>
  <div class="card mt-4">
    <div class="card-header">
      <h2 class="card-title">{{ T.loginSignupHeader }}</h2>
    </div>
    <div class="card-body">
      <form>
        <div class="row justify-content-md-center">
          <div class="col-md-4 col-md-offset-2">
            <div class="form-group">
              <label class="control-label">{{ T.wordsUser }}</label>
              <input
                v-model="username"
                data-signup-username
                name="reg_username"
                class="form-control"
                autocomplete="username"
              />
            </div>
          </div>
          <div class="col-md-4">
            <div class="form-group">
              <label class="control-label">{{ T.loginEmail }}</label>
              <input
                v-model="email"
                data-signup-email
                name="reg_email"
                type="email"
                class="form-control"
                autocomplete="email"
              />
            </div>
          </div>
        </div>
        <div class="row justify-content-md-center">
          <div class="col-md-4 col-md-offset-2">
            <div class="form-group">
              <label class="control-label">{{ T.loginPasswordCreate }}</label>
              <input
                v-model="password"
                data-signup-password
                name="reg_password"
                type="password"
                class="form-control"
                autocomplete="new-password"
              />
            </div>
          </div>
          <div class="col-md-4">
            <div class="form-group">
              <label class="control-label">{{ T.loginRepeatPassword }}</label>
              <input
                v-model="passwordConfirmation"
                data-signup-repeat-password
                name="reg_password_confirmation"
                type="password"
                class="form-control"
                autocomplete="new-password"
              />
            </div>
          </div>
        </div>
        <div class="row justify-content-md-center">
          <div class="col-md-4 col-md-offset-2">
            <omegaup-markdown
              :markdown="T.privacyPolicyNotice"
            ></omegaup-markdown>
          </div>
          <div v-if="validateRecaptcha" class="col-md-4">
            <vue-recaptcha
              name="recaptcha"
              sitekey="6LfMqdoSAAAAALS8h-PB_sqY7V4nJjFpGK2jAokS"
              @verify="verify"
              @expired="expired"
            ></vue-recaptcha>
          </div>
          <div class="col-md-4 col-md-offset-6">
            <div class="form-group">
              <button
                data-signup-submit
                class="btn btn-primary form-control"
                name="sign_up"
                @click.prevent="
                  $emit(
                    'register-and-login',
                    username,
                    email,
                    password,
                    passwordConfirmation,
                    recaptchaResponse,
                  )
                "
              >
                {{ T.loginSignUp }}
              </button>
            </div>
          </div>
        </div>
      </form>
    </div>
  </div>
</template>

<script lang="ts">
import { Vue, Component, Prop } from 'vue-property-decorator';
import omegaup_Markdown from '../Markdown.vue';
import T from '../../lang';

@Component({
  components: {
    'omegaup-markdown': omegaup_Markdown,
  },
})
export default class Signup extends Vue {
  @Prop() validateRecaptcha!: boolean;

  T = T;
  username: string = '';
  email: string = '';
  password: string = '';
  passwordConfirmation: string = '';
  recaptchaResponse: string = '';

  verify(response: string): void {
    this.recaptchaResponse = response;
  }

  expired(): void {
    this.recaptchaResponse = '';
  }
}
</script>
