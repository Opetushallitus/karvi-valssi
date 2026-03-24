const ValidateEmail = (email: string) => {
    const regex =
        /^[_A-Za-z0-9-+!#$%&\\'/=?^{|}~]+(.[_A-Za-z0-9-+!#$%&'*/=?^{|}~]+)@[A-Za-z0-9][A-Za-z0-9-]+(.[A-Za-z0-9-]+)*(.[A-Za-z]{2,})$/;
    return regex.test(String(email).toLowerCase());
};

export default ValidateEmail;
