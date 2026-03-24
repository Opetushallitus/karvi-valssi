import {OppilaitosSetType} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import {
    CheckBoxType,
    QuestionAnswersType,
} from '@cscfi/shared/services/Data/Data-service';

export const aluejakoData: OppilaitosSetType = {
    grouped: [
        {
            id: '11',
            name: {fi: 'alue1', sv: 'grupp1'},
            oppilaitokset: [
                {oid: '1.1', name: {fi: 'ol1', sv: 'dh1'}},
                {oid: '1.2', name: {fi: 'ol2', sv: 'dh2'}},
            ],
        },
        {
            id: '22',
            name: {fi: 'alue2', sv: 'grupp2'},
            oppilaitokset: [
                {oid: '2.1', name: {fi: 'ol3', sv: 'dh3'}},
                {oid: '2.2', name: {fi: 'ol4', sv: 'dh4'}},
            ],
        },
    ],
    ungrouped: [
        {
            id: null,
            name: {fi: '', sv: ''},
            oppilaitokset: [
                {oid: '0.1', name: {fi: 'ol5', sv: 'dh5'}},
                {oid: '0.2', name: {fi: 'ol6', sv: 'dh6'}},
            ],
        },
    ],
};

export const monivalintaRaporttiData: {
    questions: CheckBoxType[];
    answers: QuestionAnswersType;
} = {
    questions: [
        {
            id: 0,
            title: {fi: 'ensimmäinen kysymys', sv: ''},
            checked: false,
            description: {fi: '', sv: ''},
        },
        {
            id: 1,
            title: {fi: 'toinen kysymys', sv: ''},
            checked: false,
            description: {fi: '', sv: ''},
        },
        {
            id: 2,
            title: {fi: 'kolmas kysymys', sv: ''},
            checked: false,
            description: {fi: '', sv: ''},
        },
    ],
    answers: {
        answers_available: true,
        answers_count: 6,
        answers_int: [3, 4, 3],
        answers_pct: [50, 67, 50],
        answers_sum: 10,
    },
};
