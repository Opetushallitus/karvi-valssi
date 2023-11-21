import {format} from 'date-fns';
import {switchMap, tap} from 'rxjs';

import {KyselyType, TextType} from '@cscfi/shared/services/Data/Data-service';
import AlertService, {AlertType} from '@cscfi/shared/services/Alert/Alert-service';
import {
    arvoAddKysely$,
    arvoAddKyselykerta$,
    ArvoKysely,
    ArvoKyselyKertaPost,
    ArvoKyselyPost,
    arvoPublishKysely$,
} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import {
    FormType,
    TyontekijatType,
    VirkailijapalveluKyselyResponseType,
    VirkailijapalveluKyselySendObject,
    virkailijapalveluSendKysely$,
} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import {UserInfoType} from '@cscfi/shared/services/Login/Login-service';

const SendKysely = (
    userinfo: UserInfoType,
    formData: FormType,
    kyselykertaId: number | undefined,
    kysely: KyselyType | null,
    navigate: any,
    navigateToTiedonkeruu: boolean,
    emailSubject: TextType,
) => {
    const navigateAway = () => {
        if (navigateToTiedonkeruu) {
            navigate('/tiedonkeruu');
        } else {
            navigate('/');
        }
    };

    const createArvoKysymysPost = (
        kysymysryhma: KyselyType,
        data: any,
    ): ArvoKyselyPost => ({
        nimi_fi: emailSubject.fi,
        nimi_sv: emailSubject.sv,
        voimassa_alkupvm: format(new Date(data?.startDate!), 'yyyy-MM-dd'),
        voimassa_loppupvm: format(new Date(data?.endDate!), 'yyyy-MM-dd'),
        kysymysryhmat: [
            {
                kysymysryhmaid: kysymysryhma.id,
            },
        ],
        metatiedot: {
            valssi_saate: '', // saate not needed for queries sent by paakayttaja
            valssi_kysymysryhma: kysymysryhma.id,
        },
    });
    const createArvoKyselyKertaPost = (ak: ArvoKysely): ArvoKyselyKertaPost => ({
        kyselyid: ak.kyselyid,
        kyselykerta: {
            voimassa_alkupvm: ak.voimassa_alkupvm,
            voimassa_loppupvm: ak.voimassa_loppupvm,
            nimi: ak.nimi_fi,
        },
    });
    let tyontekijat: TyontekijatType[] = [];
    if (formData.tyontekijat) {
        let tyontekijatList = formData.tyontekijat.replaceAll(';', ',');

        tyontekijatList = tyontekijatList.replaceAll('\n', '');
        tyontekijatList = tyontekijatList.replaceAll('\r', '');
        tyontekijatList = tyontekijatList.replaceAll(' ', '');
        const tyontekijatListListSplited = tyontekijatList.split(',');

        tyontekijat = tyontekijatListListSplited.map((email: string) => ({
            email,
        }));
    }
    if (formData.generatedEmails) {
        tyontekijat = formData.generatedEmails?.map((item: any) => ({
            email: item.email,
            tyontekija_id: item.tyontekija_id,
        }));
    }
    if (kyselykertaId) {
        // create vastaajatunnus for existing kyselykerta
        const body: VirkailijapalveluKyselySendObject = {
            kyselykerta: kyselykertaId,
            voimassa_alkupvm: format(new Date(formData.startDate!), 'yyyy-MM-dd'),
            voimassa_loppupvm: format(new Date(formData.endDate!), 'yyyy-MM-dd'),
            message: formData.message,
            tyontekijat,
        };

        virkailijapalveluSendKysely$(userinfo!)(body).subscribe(
            (response: VirkailijapalveluKyselyResponseType) => {
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
        );
    } else {
        // create kysely + kyselykerta

        // TODO: why not use arvoMassAddKysely$
        arvoAddKysely$(createArvoKysymysPost(kysely!, formData)).subscribe({
            next: (uusikysely) => {
                arvoPublishKysely$(uusikysely.kyselyid)
                    .pipe(
                        switchMap((julkaistukysely) =>
                            arvoAddKyselykerta$(
                                createArvoKyselyKertaPost(julkaistukysely),
                            ),
                        ),
                        tap((result) => {
                            const body: VirkailijapalveluKyselySendObject = {
                                kyselykerta: result.kyselykertaid,
                                voimassa_alkupvm: format(
                                    new Date(formData?.startDate!),
                                    'yyyy-MM-dd',
                                ),
                                voimassa_loppupvm: format(
                                    new Date(formData?.endDate!),
                                    'yyyy-MM-dd',
                                ),
                                message: formData.message,
                                tyontekijat,
                            };
                            virkailijapalveluSendKysely$(userinfo!)(body).subscribe(
                                (response: VirkailijapalveluKyselyResponseType) => {
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
                            );
                        }),
                    )
                    .subscribe(() => {});
            },
            complete: () => {
                console.log('complete');
            },
            error: () => {
                console.log('error');
                // TODO VAL-368
                // if something goes wrong in creating kysely, publishing it, creating kyselykerta and sending email
                // wrapping all this to a single transaction would be a solution -> might require a new backend
                // endpoint handling all the steps, using a direct access to database = rollback possibility
                // Also add redirect to frontpage with notification (AlertService)
            },
        });
    }
};
export default SendKysely;
