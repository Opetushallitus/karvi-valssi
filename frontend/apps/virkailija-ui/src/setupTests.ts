// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';
import {addI18nResources, initI18n} from '@cscfi/shared/test-utils';

const INITIAL_TRANSLATION = {};

beforeAll(() => {
    initI18n(INITIAL_TRANSLATION);
});

afterEach(() => {
    // this would remove all existing translation and load initial one.
    addI18nResources(INITIAL_TRANSLATION);
});
