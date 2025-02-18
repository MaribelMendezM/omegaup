<template>
  <tags-input
    v-model="selectedOptions"
    :existing-tags="existingOptions"
    :typeahead="true"
    :typeahead-style="'dropdown'"
    :typeahead-max-results="maxResults"
    :typeahead-activation-threshold="activationThreshold"
    :placeholder="T.typeaheadSearchPlaceholder"
    :limit="1"
    :hide-input-on-limit="true"
    :only-existing-tags="true"
    :typeahead-hide-discard="true"
    @change="updateExistingOptions"
    @tag-added="onTagAdded"
    @tag-removed="onTagRemoved"
  >
  </tags-input>
</template>

<script lang="ts">
import { Vue, Component, Prop, Watch } from 'vue-property-decorator';
import VoerroTagsInput from '@voerro/vue-tagsinput';
import '@voerro/vue-tagsinput/dist/style.css';
import T from '../../lang';
import { types } from '../../api_types';

@Component({
  components: {
    'tags-input': VoerroTagsInput,
  },
})
export default class Typeahead extends Vue {
  @Prop() existingOptions!: types.ListItem[];
  @Prop({ default: 3 }) activationThreshold!: number;
  @Prop({ default: 5 }) maxResults!: number;
  @Prop({ default: null }) value!: null | string;

  T = T;
  selectedOptions: types.ListItem[] = [];

  updateExistingOptions(query: string): void {
    if (query.length < this.activationThreshold) return;
    this.$emit('update-existing-options', query);
  }

  onTagAdded(): void {
    if (this.selectedOptions.length < 1) return;
    this.$emit('update:value', this.selectedOptions[0].key);
  }

  onTagRemoved(): void {
    this.$emit('update:value', null);
  }

  @Watch('value')
  onValueChanged(newValue: null | string): void {
    if (!newValue) {
      this.selectedOptions = [];
      return;
    }
    this.existingOptions.push({ value: newValue, key: newValue });
    this.selectedOptions = this.existingOptions.filter(
      (option) => option.key === newValue,
    );
  }
}
</script>

<style lang="scss">
@import '../../../../sass/main.scss';

.tags-input-remove::before,
.tags-input-remove::after,
.tags-input-typeahead-item-highlighted-default {
  background-color: $omegaup-primary--darker;
}

.tags-input-wrapper-default {
  height: 38px;
}
</style>
