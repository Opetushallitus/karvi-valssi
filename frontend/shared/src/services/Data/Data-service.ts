/*
TODO: Tämän palvelun uudelleennimeäminen /-ryhmittely
      https://jira.ci.csc.fi/browse/VAL-54
*/

import ArvoInputTypes, {
    PaaIndikaattoriType,
} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import InputTypes from '../../components/InputType/InputTypes';

export interface TextType {
    fi: string;
    sv: string;
}

export interface CheckBoxType {
    id: number;
    title: TextType;
    checked: boolean;
    description?: TextType;
}

export interface RadioButtonType {
    id: number;
    title: TextType;
    checked: boolean;
    description?: TextType;
}
export type MatrixScaleType = TextType & {
    value: number;
};
export type MatrixType = {
    name: string;
    order_no: number;
    label: TextType;
    min_value: number;
    max_value: number;
    default_value: number;
    step_count: number;
    eos_value?: MatrixScaleType;
    scale: MatrixScaleType[];
};
export type MatrixQuestionScaleType = {
    fi: string;
    sv: string;
    value: number;
};
export type QuestionAnswersType = {
    answers_available: Array<number | string>;
    answers_average: Array<number | string>;
    answers_int: Array<Array<number>>;
    answers_pct: Array<number | string>;
    answers_sum: Array<number | string>;
};
export interface KysymysType {
    id: number;
    inputType: InputTypes;
    title: TextType;
    description: TextType;
    required: boolean;
    allowEos?: boolean;
    answerOptions: CheckBoxType[];
    matrixQuestions: KysymysType[];
    answerType?: ArvoInputTypes;
    isMatrixQuestionRoot?: boolean;
    matrixRootId?: number;
    hidden?: boolean;
    order?: number;
    matrix_question_scale?: Array<MatrixQuestionScaleType>;
    question_answers?: QuestionAnswersType;
}

export enum StatusType {
    luonnos = 'luonnos',
    julkaistu = 'julkaistu',
    arkistoitu = 'arkistoitu',
    suljettu = 'suljettu',
}

export interface KyselyType {
    id: number;
    topic: TextType;
    kysymykset: KysymysType[];
    status: StatusType;
    lomaketyyppi: string;
    paaIndikaattori: PaaIndikaattoriType;
    sekondaariset_indikaattorit?: any;
    muutettuaika?: string; // date
    oppilaitos?: string | undefined | null;
    lastKyselysend?: any;
    kyselykertaid?: number;
    voimassaLoppupvm?: Date;
}

export type GenericFormValueType = {
    [key: string]: string | number | boolean | Object;
};

export type KyselyVastaus = {
    kysymysid: string;
    kyselyKerta?: string;
    string?: string;
    numerovalinta?: number;
    en_osaa_sanoa?: number;
};
