import {describe, test, expect} from 'vitest';
import * as Settings from './Settings-service';

describe('Settings', () => {
    test('it should exist', () => {
        expect(Settings.arvoHostname).toBeTruthy();
    });
    test('it should give prod specific env value', () => {
        Settings.currentEnvironment.isProd = true;
        const opintopolkuBase = Settings.getEnv(
            import.meta.env.VITE_APP_OPINTOPOLKU_HOSTNAME,
            import.meta.env.VITE_APP_OPINTOPOLKU_HOSTNAME_PROD,
        );
        expect(opintopolkuBase).toEqual('https://virkailija.opintopolku.fi/');
    });
    test('it should give qa specific env value', () => {
        Settings.currentEnvironment.isProd = false;
        const opintopolkuBase = Settings.getEnv(
            import.meta.env.VITE_APP_OPINTOPOLKU_HOSTNAME,
            import.meta.env.VITE_APP_OPINTOPOLKU_HOSTNAME_PROD,
        );
        // Localhost so we dont do queries to external environments during tests
        expect(opintopolkuBase).toEqual('http://localhost/');
    });
});
