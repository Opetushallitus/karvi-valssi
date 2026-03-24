// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom/vitest';
import {vi, beforeAll, afterEach} from 'vitest';
import {of} from 'rxjs';
import {addI18nResources, initI18n} from './test-utils';

const INITIAL_TRANSLATION = {};

beforeAll(() => {
    vi.mock('components/Markdown/MarkdownWrapper', () => ({
        default: 'components/Markdown/MarkdownWrapperMock',
    }));

    vi.mock('@cscfi/shared/services/Lokalisointi/Lokalisointi-service', () => ({
        default: () => of([]),
    }));
    vi.mock('@cscfi/shared/services/http/http-service', () => ({
        arvoHttp: {
            get: () => of(),
            getWithCache: () => of(),
            post: () => of(),
        },
        raportointipalveluHttp: {
            getWithCache: () => of(),
        },
        virkailijapalveluHttp: {
            getWithCache: () => of(),
        },
        commonHttp: {
            getWithCache: () => of(),
        },
    }));

    initI18n(INITIAL_TRANSLATION);
});

afterEach(() => {
    // this would remove all existing translation and load initial one.
    addI18nResources(INITIAL_TRANSLATION);
});
