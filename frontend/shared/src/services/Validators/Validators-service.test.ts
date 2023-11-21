import ValidateEmail from './Validators-service';

describe('Validators', () => {
    test('it should return true for valid email', () => {
        expect(ValidateEmail('joku@email.com')).toBe(true);
        expect(ValidateEmail('joku.jossain@email.com')).toBe(true);
        // valid email but not recommended: local domain name with no TLD,
        // although ICANN highly discourages dotless email addresses
        expect(ValidateEmail('joku@email')).toBe(true);
    });
    test('it should return false for invalid email', () => {
        expect(ValidateEmail('testi')).toBe(false);
        expect(ValidateEmail('testi@')).toBe(false);
        expect(ValidateEmail('@testi')).toBe(false);
    });
});
