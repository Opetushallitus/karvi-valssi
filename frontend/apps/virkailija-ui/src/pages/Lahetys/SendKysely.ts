import {format} from 'date-fns';
import {KyselyType, TextType} from '@cscfi/shared/services/Data/Data-service';
import AlertService, {AlertType} from '@cscfi/shared/services/Alert/Alert-service';
import {
    arvoAddKysely$,
    ArvoKyselyPost,
} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import {
    FormType,
    TyontekijatType,
    VirkailijapalveluKyselyResponseType,
    VirkailijapalveluKyselySendObject,
    virkailijapalveluSendKysely$,
} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import {UserInfoType} from '@cscfi/shared/services/Login/Login-service';
import {AjaxError} from 'rxjs/ajax';
import {toJson} from '@cscfi/shared/services/Http/Http-service';
import * as ErrorService from '@cscfi/shared/services/Error/Error-service';

const SendKysely = (
    userinfo: UserInfoType,
    formData: FormType,
    kyselykertaId: number | undefined,
    kysely: KyselyType | null,
    navigate: any,
    navigateToTiedonkeruu: boolean,
    emailSubjectFn: (nameExtender?: number) => TextType,
) => {
    const navigateAway = () => {
        if (navigateToTiedonkeruu) {
            navigate('/tiedonkeruu');
        } else {
            navigate('/');
        }
    };

    const createArvoKyselyPost = (
        kysymysryhma: KyselyType,
        nameExtender?: number | undefined,
    ) => {
        const alkupvm = format(new Date(formData?.startDate), 'yyyy-MM-dd');
        const loppupvm = format(new Date(formData?.endDate), 'yyyy-MM-dd');
        const subject = emailSubjectFn(nameExtender);

        return {
            tila: 'julkaistu',
            voimassa_alkupvm: alkupvm,
            voimassa_loppupvm: loppupvm,
            nimi_fi: subject.fi,
            nimi_sv: subject.sv,
            tyyppi: kysymysryhma.lomaketyyppi,
            metatiedot: {
                valssi_kysymysryhma: kysymysryhma.id,
            },
            kyselykerrat: [
                {
                    nimi: subject.fi,
                    voimassa_alkupvm: alkupvm,
                    voimassa_loppupvm: loppupvm,
                },
            ],
            kysymysryhmat: [
                {
                    kysymysryhmaid: kysymysryhma.id,
                },
            ],
        } as ArvoKyselyPost;
    };

    let tyontekijat: TyontekijatType[] = [];
    if (formData.tyontekijat) {
        let tyontekijatList = formData.tyontekijat
            .replaceAll(';', ',')
            .replaceAll('\r\n', ',')
            .replaceAll('\n', ',')
            .replaceAll('\r', ',');

        tyontekijatList = tyontekijatList.replaceAll(' ', '');
        const tyontekijatListListSplited = tyontekijatList
            .split(',')
            .filter((s) => s !== '');

        tyontekijat = tyontekijatListListSplited.map((email: string) => ({
            email,
        }));
    }
    if (formData.generatedEmails && formData.generatedEmails.length > 0) {
        tyontekijat = formData.generatedEmails?.map(
            (item) =>
                ({
                    email: item.email,
                    tyontekija_id: item.tyontekija_id,
                }) as TyontekijatType,
        ) as TyontekijatType[];
    }

    const kyselySendBody = (kkId: number) =>
        ({
            kyselykerta: kkId,
            voimassa_alkupvm: format(new Date(formData.startDate!), 'yyyy-MM-dd'),
            voimassa_loppupvm: format(new Date(formData.endDate!), 'yyyy-MM-dd'),
            message: formData.message,
            tyontekijat,
        }) as VirkailijapalveluKyselySendObject;

    const virkailijaPalveluSendKysely = (kkId: number) => {
        virkailijapalveluSendKysely$(userinfo!)(kyselySendBody(kkId)).subscribe({
            next: (response: VirkailijapalveluKyselyResponseType) => {
                const alert = {
                    title: {
                        key: 'kysely-on-lahetetty',
                        ns: 'lahetys',
                        lahetetty: response.created,
                    },
                    severity: 'success',
                } as AlertType;
                AlertService.showAlert(alert);
                navigateAway();
            },
            error: () => {
                console.error('kyselysend failed');
            },
        });
    };

    const handleCreateKysely = (retryCounter = 0) => {
        const maxRetry = 2;

        arvoAddKysely$(
            createArvoKyselyPost(
                kysely!,
                retryCounter > 0 ? retryCounter + 1 : undefined,
            ),
        ).subscribe({
            next: (newKysely) => {
                const kkfirst = newKysely.kyselykerrat.find((first) => !!first);

                // todo: reponse doesn't have kyselykertaid

                if (kkfirst?.kyselykertaid) {
                    virkailijaPalveluSendKysely(kkfirst.kyselykertaid);
                } else {
                    console.error('kyselykerta not found, kyselysend failed');
                }
            },
            error: (error: AjaxError) => {
                const errorMsgRaw: string | string[] = toJson(error.response);
                const sameNameError = 'kysely.samanniminen_kysely';
                const isSameNameError = Array.isArray(errorMsgRaw)
                    ? errorMsgRaw.some((errorMsg: string) =>
                          errorMsg.startsWith(sameNameError),
                      )
                    : errorMsgRaw.startsWith(sameNameError);

                if (error.status === 400 && isSameNameError) {
                    if (retryCounter <= maxRetry) {
                        console.info(
                            'Questionnaire with same name found, let´s try again',
                            retryCounter,
                        );
                        handleCreateKysely(retryCounter + 1);
                    } else {
                        console.error(
                            'Questionnaire with same name found and retry count has exceeded',
                            retryCounter,
                        );
                        ErrorService.addHttpError(error, {
                            400: {
                                severity: 'error',
                                title: {key: 'alert-error-title', ns: 'lahetys'},
                                body: {
                                    key: 'alert-error-body-same-name-count-exceeded',
                                    ns: 'lahetys',
                                },
                            } as AlertType,
                        });
                    }
                } else if ([400, 404].includes(error.status)) {
                    ErrorService.addHttpError(error, {
                        400: {
                            severity: 'error',
                            title: {key: 'alert-error-title', ns: 'lahetys'},
                            body: {key: '400-general-body', ns: 'alert'},
                        } as AlertType,
                        404: {
                            severity: 'error',
                            title: {key: 'alert-error-title', ns: 'lahetys'},
                            body: {key: '404-general-body', ns: 'alert'},
                        } as AlertType,
                    });
                }
            },
        });
    };

    if (kyselykertaId) {
        // create vastaajatunnus for existing kyselykerta
        virkailijaPalveluSendKysely(kyselykertaId);
    } else {
        // create kysely + kyselykerta

        handleCreateKysely();
    }
};
export default SendKysely;
