import {describe, test, expect} from 'vitest';
import * as Login from './Login-service';
import {AllowedRole, ArvoRoles} from './Login-service';

describe('Login', () => {
    test('it should give url with null param', () => {
        const loginUrl = Login.casLoginUrl(null);
        expect(loginUrl).toBe(
            'http://localhost/cas/login?service=http://localhost:3000/virkailija-ui/login',
        );
    });
    test('it should give url with slash param', () => {
        const loginUrl = Login.casLoginUrl('/');
        expect(loginUrl).toBe(
            'http://localhost/cas/login?service=http://localhost:3000/virkailija-ui/',
        );
    });
    test('it should give url with path param', () => {
        const loginUrl = Login.casLoginUrl('/indikaattorit');
        expect(loginUrl).toBe(
            'http://localhost/cas/login?service=http://localhost:3000/virkailija-ui/indikaattorit',
        );
    });
    test('it should allow user access with proper role', () => {
        const allowedRoles = {arvo: [ArvoRoles.YLLAPITAJA]} as AllowedRole;
        const userRole = {
            kayttooikeus: 'YLLAPITAJA',
            service: 'arvo',
        };
        const userRoles: Array<Login.Role> = [userRole];
        const isAllowedAccess = Login.hasRequiredRole(allowedRoles, userRoles);
        expect(isAllowedAccess).toBe(true);
    });
    test('it should allow user access with multiple roles', () => {
        const allowedRoles = {arvo: [ArvoRoles.PAAKAYTTAJA]};
        const userRole1 = {
            kayttooikeus: ArvoRoles.PAAKAYTTAJA,
            service: 'arvo',
        };
        const userRole2 = {
            kayttooikeus: ArvoRoles.TOTEUTTAJA,
            service: 'arvo',
        };
        const userRoles: Array<Login.Role> = [userRole1, userRole2];
        const isAllowedAccess = Login.hasRequiredRole(allowedRoles, userRoles);
        expect(isAllowedAccess).toBe(true);
    });
    test('it should allow user access with multiple allowed roles', () => {
        const allowedRoles = {arvo: [ArvoRoles.TOTEUTTAJA, ArvoRoles.YLLAPITAJA]};
        const userRole = {
            kayttooikeus: 'YLLAPITAJA',
            service: 'arvo',
        };
        const userRoles: Array<Login.Role> = [userRole];
        const isAllowedAccess = Login.hasRequiredRole(allowedRoles, userRoles);
        expect(isAllowedAccess).toBe(true);
    });
    test('it should allow user access with multiple allowed services', () => {
        const allowedRoles = {
            arvo: [ArvoRoles.YLLAPITAJA],
            otherService: [ArvoRoles.TOTEUTTAJA],
        };
        const userRole = {
            kayttooikeus: 'YLLAPITAJA',
            service: 'arvo',
        };
        const userRoles: Array<Login.Role> = [userRole];
        const isAllowedAccess = Login.hasRequiredRole(allowedRoles, userRoles);
        expect(isAllowedAccess).toBe(true);
    });
    test('it should not allow user access without roles', () => {
        const allowedRoles = {arvo: [ArvoRoles.YLLAPITAJA]};
        const userRoles: Array<Login.Role> = [];
        const isAllowedAccess = Login.hasRequiredRole(allowedRoles, userRoles);
        expect(isAllowedAccess).toBe(false);
    });
    test('it should not allow user access without roles even with empty allowed roles', () => {
        const allowedRoles = {};
        const userRoles: Array<Login.Role> = [];
        const isAllowedAccess = Login.hasRequiredRole(allowedRoles, userRoles);
        expect(isAllowedAccess).toBe(false);
    });
    test('it should not allow user access with role to wrong service', () => {
        const allowedRoles = {arvo: [ArvoRoles.YLLAPITAJA]};
        const userRole = {
            kayttooikeus: 'YLLAPITAJA',
            service: 'wrong_service',
        };
        const userRoles: Array<Login.Role> = [userRole];
        const isAllowedAccess = Login.hasRequiredRole(allowedRoles, userRoles);
        expect(isAllowedAccess).toBe(false);
    });
    test('it should not allow user access with role to wrong role', () => {
        const allowedRoles = {arvo: [ArvoRoles.YLLAPITAJA]};
        const userRole = {
            kayttooikeus: 'KAYTTAJA',
            service: 'arvo',
        };
        const userRoles: Array<Login.Role> = [userRole];
        const isAllowedAccess = Login.hasRequiredRole(allowedRoles, userRoles);
        expect(isAllowedAccess).toBe(false);
    });
});
