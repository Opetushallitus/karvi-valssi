export const isNumeric: RegExp = /^((0?|[1-9]\d*)[.,][0-9]+)$|^(0?|[1-9]\d*)$/i;

// https://github.com/Opetushallitus/varda/blob/oph-public-branch/webapps/varda/validators.py#L16
export const isValidEmail: RegExp =
    /^[_A-Za-z0-9-+!#$%&'*/=?^`{|}~]+(\.[_A-Za-z0-9-+!#$%&'*/=?^`{|}~]+)*@[A-Za-z0-9][A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*(\.[A-Za-z]{2,})$/i; // eslint-disable-line
export const isValidEmailList: RegExp =
    /^[\r\n]*(([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5}){1,25})+(\s*[//,.,;.]\s*(([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5}){1,25})+)*[\r\n]*$/; // eslint-disable-line

export const isOid: RegExp = /^([0-2])((\.0)|(\.[1-9][0-9]*))*$/gm;
