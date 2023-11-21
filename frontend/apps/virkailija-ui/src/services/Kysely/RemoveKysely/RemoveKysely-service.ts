import AlertService, {AlertType} from '@cscfi/shared/services/Alert/Alert-service';
import {arvoDeleteHttp$} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';

const removeKysely = (kyselyId: number, name: string) => {
    arvoDeleteHttp$(`kysymysryhma/${kyselyId}`).subscribe({
        error(err) {
            const alert = {
                title: {key: 'kysely-remove-failure-title', ns: 'alert'},
                severity: 'error',
                body: {key: 'kysely-remove-failure-body', ns: 'alert', name, kyselyId},
            } as AlertType; // no need to define bodyStrong and duration
            AlertService.showAlert(alert);
            console.log(`Error in removing kysely: ${err}`); // TODO proper logging
        },
        complete() {
            // notify user
            const alert = {
                title: {key: 'kysely-removed-title', ns: 'alert'},
                severity: 'success',
                body: {key: 'kysely-removed-body', ns: 'alert', name},
            } as AlertType;
            AlertService.showAlert(alert);
        },
    });
};

export default removeKysely;
