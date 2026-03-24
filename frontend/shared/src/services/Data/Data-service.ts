import {ArvoKysymysMetatiedotBase} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import InputTypes from '../../components/InputType/InputTypes';

export interface TextType {
    fi: string;
    sv: string;
    en?: string;
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

export interface DropdownType {
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
    en?: string;
    value: number;
};
export type QuestionAnswersType = {
    answers_available?: boolean | Array<boolean>;
    answers_average?: Array<number | string>;
    answers_count?: number;
    answers_int?: Array<Array<number>> | Array<number>;
    answers_pct?: Array<Array<number>> | Array<number>;
    answers_sum?: Array<number | string> | number;
};

type InstaQuestionType = {
    kysymys_fi: string;
};

export type FollowUpDataType = {
    [index: number]: InstaQuestionType;
};

export type FollowupQuestionsType = {
    [index: number | string]: KysymysType;
};

export type FollowupToType = {
    questionId: number;
    questionAnswer: string;
};

enum ArvoInputTypes {
    monivalinta = 'monivalinta',
    string = 'string',
    matrix_root = 'matrix_root',
}

export interface KysymysType {
    id: number;
    inputType: InputTypes;
    title: TextType;
    description: TextType;
    required: boolean;
    allowEos?: boolean;
    answerOptions: CheckBoxType[];
    matrixQuestions: KysymysType[];
    followupQuestions?: FollowupQuestionsType;
    followupTo?: FollowupToType;
    answerType?: ArvoInputTypes;
    isMatrixQuestionRoot?: boolean;
    matrixRootId?: number;
    hidden?: boolean;
    insta?: boolean;
    order?: number;
    pagebreak: boolean;
    page: number;
    matrix_question_scale?: Array<MatrixQuestionScaleType>;
    question_answers?: QuestionAnswersType;
    metatiedot: ArvoKysymysMetatiedotBase;
    string_answer?: {
        fi: string;
        sv: string;
    };
}

export enum StatusType {
    luonnos = 'luonnos',
    julkaistu = 'julkaistu',
    arkistoitu = 'arkistoitu',
    lukittu = 'lukittu',
    suljettu = 'suljettu',
}

export enum HiddenType {
    notHidden = 0,
    hidden = 1,
    hiddenByCondition = 2,
}

export type PaaindikaattoriType = {
    group: number;
    key: string;
};

export type SekondaarinenIndikaattoriType = {
    key: string;
    group_id: number;
    laatutekija: string;
};
export interface KyselyType {
    id: number;
    topic: TextType;
    kysymykset: KysymysType[];
    status: StatusType;
    lomaketyyppi: string;
    paaIndikaattori: PaaindikaattoriType;
    sekondaariset_indikaattorit?: SekondaarinenIndikaattoriType[];
    muutettuaika?: string; // date
    oppilaitos?: string | undefined | null;
    lastKyselysend?: any;
    kyselykertaid?: number;
    voimassaLoppupvm?: Date;
}

export type GenericFormValueType = {
    [key: string]: string | number | boolean | Date | object | null;
};

export type KyselyVastaus = {
    kysymysid: string;
    kyselyKerta?: string;
    string?: string;
    numerovalinta?: number;
    en_osaa_sanoa?: number;
};

export type FollowupDataType = {
    kysymysid: number | null;
    inputType: InputTypes | null;
};

export enum PalauteKyselyIndikaattori {
    key = 'palautekysely',
}
export default ArvoInputTypes;
