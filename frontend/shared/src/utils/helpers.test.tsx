import {fi, sv} from 'date-fns/locale';
import {getDateFnsLocale, deepCopy} from './helpers';

describe('date-fns locale lookup', () => {
    it('shound find fi', () => {
        expect(getDateFnsLocale('fi')).toBe(fi);
    });
    it('shound find sv', () => {
        expect(getDateFnsLocale('sv')).toBe(sv);
    });
    test('deepCopy should deep copy an object', () => {
        expect(deepCopy({foo: 'bar'})).toMatchObject({foo: 'bar'});
    });
});
